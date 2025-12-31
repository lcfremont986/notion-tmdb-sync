name: Notion TMDb Sync

on:
  schedule:
    - cron: "*/15 * * * *"   # runs every 15 minutes
  workflow_dispatch:          # allows manual runs from GitHub UI

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install requests

      - name: Run TMDb → Notion sync
        env:
          TMDB_KEY: ${{ secrets.TMDB_KEY }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
        run: python tmdb_notion_sync.py
