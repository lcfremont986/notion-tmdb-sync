import requests, time

# --- CONFIG ---
TMDB_KEY = "your_tmdb_api_key_here"
NOTION_TOKEN = "secret_ntn_b216682642287radpX9fm1qNUFaPOODTe97HxGmgSwS0Kx"
NOTION_DATABASE_ID = "2570812725b6805c9a9ffcfed140ba8d"

NOTION_VERSION = "2022-06-28"

# --- STEP 1: Fetch all Notion pages ---
def get_notion_pages():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    res = requests.post(url, headers=headers)
    res.raise_for_status()
    return res.json()["results"]

# --- STEP 2: Search and fetch actor data from TMDb ---
def fetch_actor_data(name):
    search_url = f"https://api.themoviedb.org/3/search/person"
    params = {"api_key": TMDB_KEY, "query": name}
    r = requests.get(search_url, params=params)
    results = r.json().get("results", [])
    if not results:
        return None
    actor_id = results[0]["id"]

    details_url = f"https://api.themoviedb.org/3/person/{actor_id}"
    details_params = {"api_key": TMDB_KEY, "append_to_response": "movie_credits"}
    d = requests.get(details_url, params=details_params).json()

    # Extract relevant data
    actor_name = d.get("name", name)
    biography = d.get("biography", "")
    photo_url = f"https://image.tmdb.org/t/p/original{d.get('profile_path')}" if d.get("profile_path") else ""
    imdb_id = d.get("imdb_id", "")
    imdb_link = f"https://www.imdb.com/name/{imdb_id}/" if imdb_id else ""
    filmography = ", ".join(
        [f"{m['title']} ({m.get('release_date', '')[:4]})"
         for m in d.get("movie_credits", {}).get("cast", [])[:5]]
    )

    return {
        "name": actor_name,
        "bio": biography,
        "photo": photo_url,
        "filmography": filmography,
        "imdb_id": imdb_id,
        "imdb_link": imdb_link
    }

# --- STEP 3: Update Notion page ---
def update_notion_page(page_id, actor):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    data = {
        "properties": {
            "Biography": {"rich_text": [{"text": {"content": actor["bio"]}}]},
            "Photo": {"url": actor["photo"]},
            "Filmography": {"rich_text": [{"text": {"content": actor["filmography"]}}]},
            "IMDb ID": {"rich_text": [{"text": {"content": actor["imdb_id"]}}]},
            "IMDb Link": {"url": actor["imdb_link"]}
        }
    }
    r = requests.patch(url, headers=headers, json=data)
    return r.status_code == 200

# --- STEP 4: Run sync loop ---
def sync_loop():
    while True:
        print("🔄 Checking Notion database for missing actor info...")
        pages = get_notion_pages()
        for page in pages:
            props = page["properties"]
            name = props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else None
            bio = props.get("Biography", {}).get("rich_text", [])
            if not name or bio:  # skip if no name or already filled
                continue

            print(f"🎬 Fetching data for {name}...")
            actor_data = fetch_actor_data(name)
            if actor_data:
                success = update_notion_page(page["id"], actor_data)
                print(f"✅ Updated {name} in Notion!" if success else f"⚠️ Failed to update {name}.")
            else:
                print(f"❌ Could not find {name} on TMDb.")
        print("⏸ Waiting 10 minutes before next sync...\n")
        time.sleep(600)  # every 10 minutes

# --- START ---
if __name__ == "__main__":
    sync_loop()
