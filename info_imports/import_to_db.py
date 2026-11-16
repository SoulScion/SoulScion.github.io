import os
import json
import mysql.connector
from dotenv import load_dotenv

# Reuse the connection and helper functions from collect_rawg.py
from info_imports.collect_rawg import (
    get_db_connection, 
    get_existing_game_ids,
    get_or_insert_publisher, 
    get_or_insert_developer, 
    get_or_insert_genre, 
    get_or_insert_platform,
    PLATFORM_TYPE_MAPPING
)

load_dotenv()

def get_or_insert_game(connection, game, publisher_id):
    """Inserts a game and returns its database ID."""
    cursor = connection.cursor()

    # Extract release date safely (RAWG sometimes has None or "YYYY-MM-DD")
    release_date = game.get("released")
    if not release_date or release_date == "None":
        release_date = None

    cursor.execute("""
        INSERT IGNORE INTO games 
            (rawg_id, publisher_id, title, earliest_release, game_engine)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        game.get("id"),
        publisher_id,
        game.get("name", "Unknown"),
        release_date,
        None # RAWG doesn't typically provide game engine directly in this endpoint
    ))

    cursor.execute("SELECT game_id FROM games WHERE rawg_id = %s", (game.get("id"),))
    game_id = cursor.fetchone()[0]
    cursor.close()
    return game_id

def link_game_developer(connection, game_id, developer_id):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT IGNORE INTO game_credits (game_id, developer_id)
        VALUES (%s, %s)
    """, (game_id, developer_id))
    cursor.close()

def link_game_genre(connection, game_id, genre_id):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT IGNORE INTO game_genres (game_id, genre_id)
        VALUES (%s, %s)
    """, (game_id, genre_id))
    cursor.close()

def link_game_platform(connection, game_id, platform_id):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT IGNORE INTO game_availability (game_id, platform_id)
        VALUES (%s, %s)
    """, (game_id, platform_id))
    cursor.close()

def import_data():
    connection = get_db_connection()
    if not connection.is_connected():
        print("Failed to connect.")
        return

    # 1. Load the JSON
    print("Loading rawg_games.json...")
    try:
        with open("rawg_games.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("Error: rawg_games.json not found. Please run collect_rawg.py first.")
        return

    # 2. Get existing games to avoid duplicating work
    existing_ids = get_existing_game_ids(connection)
    print(f"Found {len(existing_ids)} games already in the database.")

    total_inserted = 0
    
    # 3. Loop through the games
    for game in games_data:
        rawg_id = game.get("id")
        
        # Skip if we already imported this game
        if rawg_id in existing_ids:
            continue

        print(f"Importing: {game.get('name')}")

        try:
            # --- PUBLISHERS ---
            publisher_id = None
            publishers = game.get("publishers", [])
            if publishers:
                # Just take the first publisher to keep it simple
                pub = publishers[0]
                # Ensure they have an ID, otherwise your SQL will fail on UNIQUE constraint
                if "id" in pub:
                    publisher_id = get_or_insert_publisher(connection, pub)

            # --- GAMES ---
            game_id = get_or_insert_game(connection, game, publisher_id)
            total_inserted += 1

            # --- DEVELOPERS ---
            developers = game.get("developers", [])
            for dev in developers:
                if "id" in dev:
                    dev_id = get_or_insert_developer(connection, dev)
                    link_game_developer(connection, game_id, dev_id)

            # --- GENRES ---
            genres = game.get("genres", [])
            for genre in genres:
                genre_id = get_or_insert_genre(connection, genre)
                link_game_genre(connection, game_id, genre_id)

            # --- PLATFORMS ---
            platforms = game.get("platforms", [])
            for platform_wrapper in platforms:
                platform = platform_wrapper.get("platform", {})
                
                if not platform:
                    continue

                # Check if the platform is in our mapping. 
                # If we insert None into the 'type' column, your SQL CHECK constraint will crash the script.
                slug = platform.get("slug")
                if slug in PLATFORM_TYPE_MAPPING:
                    plat_id = get_or_insert_platform(connection, platform)
                    link_game_platform(connection, game_id, plat_id)
                else:
                    # Optionally, you could insert it as 'Other' if you modify your schema
                    pass 

        except Exception as e:
            print(f"  [!] Error importing {game.get('name')}: {e}")
            # Rollback the failed game so we don't corrupt the database
            connection.rollback()
            continue

    connection.commit()
    connection.close()
    print(f"\nImport complete! Successfully added {total_inserted} new games.")

if __name__ == "__main__":
    import_data()