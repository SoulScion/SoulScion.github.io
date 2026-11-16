import os
import json
import time
import requests
from dotenv import load_dotenv
from info_imports.collect_rawg import get_db_connection, rawg_get

load_dotenv()

def get_or_insert_dlc(connection, game_id, name, rawg_additions_id):
    """
    Insert a DLC if it doesn't already exist.
    Returns True if inserted, False if already present.
    """
    cursor = connection.cursor()
    
    # Check for existing DLC by game_id + name (case-insensitive)
    cursor.execute("""
        SELECT dlc_id FROM dlcs
        WHERE game_id = %s AND LOWER(name) = LOWER(%s)
    """, (game_id, name))
    existing = cursor.fetchone()
    
    if existing:
        cursor.close()
        return False
    
    # Insert new DLC with NULL price (RAWG doesn't provide prices)
    cursor.execute("""
        INSERT INTO dlcs (game_id, name, regular_price)
        VALUES (%s, %s, NULL)
    """, (game_id, name))
    
    cursor.close()
    return True

def import_dlcs():
    connection = get_db_connection()
    if not connection.is_connected():
        print("Failed to connect to DB.")
        return

    # 1. Load the JSON to get rawg_ids
    print("Loading rawg_games.json...")
    try:
        with open("rawg_games.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("Error: rawg_games.json not found.")
        return

    # 2. Map rawg_id -> game_id from the database
    cursor = connection.cursor()
    cursor.execute("SELECT rawg_id, game_id, title FROM games")
    db_games = {str(rawg_id): (game_id, title) for rawg_id, game_id, title in cursor.fetchall()}
    cursor.close()
    print(f"Loaded {len(db_games)} games from the database.")

    total_inserted = 0
    games_processed = 0
    games_with_dlcs = 0
    failed_games = []

    # 3. Loop through each game and fetch its additions
    for index, game in enumerate(games_data, start=1):
        rawg_id = str(game.get("id"))
        if rawg_id not in db_games:
            continue

        game_id, title = db_games[rawg_id]
        games_processed += 1

        try:
            # Fetch additions for this game (paginated)
            additions = []
            page = 1
            while True:
                data = rawg_get(f"games/{rawg_id}/additions", {
                    "page": page,
                    "page_size": 40
                })
                results = data.get("results", [])
                additions.extend(results)
                
                if not data.get("next") or page >= 3:  # Cap at 3 pages per game
                    break
                page += 1
                time.sleep(0.3)

            if additions:
                games_with_dlcs += 1

            # Insert each addition as a DLC
            for addition in additions:
                name = addition.get("name", "").strip()
                if not name:
                    continue

                if get_or_insert_dlc(connection, game_id, name, addition.get("id")):
                    total_inserted += 1

            # Commit every 10 games to avoid losing progress on failure
            if games_processed % 10 == 0:
                connection.commit()
                print(f"  [{games_processed}/{len(db_games)}] "
                      f"{title}: {len(additions)} additions | "
                      f"Total DLCs inserted: {total_inserted}")

            time.sleep(0.5)  # Be polite to RAWG API

        except requests.RequestException as e:
            failed_games.append(title)
            print(f"  [!] Failed for '{title}': {e}")
            continue

    connection.commit()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Games processed:       {games_processed}")
    print(f"Games with additions:  {games_with_dlcs}")
    print(f"Total DLCs inserted:   {total_inserted}")
    print(f"Failed games:          {len(failed_games)}")
    if failed_games:
        print(f"  Failed titles: {', '.join(failed_games[:10])}")
        if len(failed_games) > 10:
            print(f"  ... and {len(failed_games) - 10} more")
    print(f"{'=' * 60}")

    connection.close()

if __name__ == "__main__":
    import_dlcs()