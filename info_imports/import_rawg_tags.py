import os
import json
from dotenv import load_dotenv
from info_imports.collect_rawg import get_db_connection

load_dotenv()

# Map RAWG tag names to your social_types table CHECK constraint values
SOCIAL_TAG_MAPPING = {
    "singleplayer": "Singleplayer",
    "multiplayer": "Multiplayer",
    "massively multiplayer": "Massively Multiplayer",
    "local co-op": "Local CO-OP",
    "online co-op": "Online CO-OP",
    "pvp": "PvP",
    "pve": "PvE",
    "co-op": "Online CO-OP", 
    # Note: We can add "Local Multiplayer", "Split Screen", etc. here later if you update the schema
}

def get_social_type_id(connection, type_name):
    """Look up the type_id from the social_types table."""
    cursor = connection.cursor()
    cursor.execute("SELECT type_id FROM social_types WHERE type_name = %s", (type_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def import_socials():
    connection = get_db_connection()
    if not connection.is_connected():
        print("Failed to connect to DB.")
        return

    # 1. Populate the social_types table first (if empty)
    cursor = connection.cursor()
    default_social_types = [
        "Singleplayer", "Multiplayer", "Massively Multiplayer", 
        "Local CO-OP", "Online CO-OP", "PvP", "PvE", "Other"
    ]
    for st in default_social_types:
        cursor.execute("INSERT IGNORE INTO social_types (type_name) VALUES (%s)", (st,))
    connection.commit()

    # 2. Load the JSON
    print("Loading rawg_games.json...")
    try:
        with open("rawg_games.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("Error: rawg_games.json not found.")
        return

    # 3. Get our database game IDs so we can link them
    cursor.execute("SELECT rawg_id, game_id FROM games")
    db_games = {str(rawg_id): game_id for rawg_id, game_id in cursor.fetchall()}
    print(f"Loaded {len(db_games)} games from the database.")

    inserted = 0
    matched_tags = 0

    # 4. Loop through games and extract tags
    for game in games_data:
        rawg_id = str(game.get("id"))
        if rawg_id not in db_games:
            continue # Game wasn't imported to DB
            
        game_id = db_games[rawg_id]
        
        # RAWG puts tags in a list of dicts: [{"id": 1, "name": "Singleplayer", "slug": "singleplayer"}, ...]
        tags = game.get("tags", [])
        
        for tag in tags:
            tag_name = tag.get("name", "").lower()
            tag_slug = tag.get("slug", "").lower()
            
            # Check if the tag name or slug is in our mapping
            mapped_type = SOCIAL_TAG_MAPPING.get(tag_name) or SOCIAL_TAG_MAPPING.get(tag_slug)
            
            if mapped_type:
                type_id = get_social_type_id(connection, mapped_type)
                if type_id:
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO game_socials (game_id, type_id)
                            VALUES (%s, %s)
                        """, (game_id, type_id))
                        if cursor.rowcount > 0:
                            inserted += 1
                        matched_tags += 1
                    except Exception as e:
                        print(f"Error linking {game.get('name')} to {mapped_type}: {e}")

    connection.commit()
    cursor.close()
    connection.close()
    print(f"\nDone! Found {matched_tags} social tags for games.")
    print(f"Inserted {inserted} new rows into game_socials.")

if __name__ == "__main__":
    import_socials()

