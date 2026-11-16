import os
import json
from dotenv import load_dotenv
from info_imports.collect_rawg import get_db_connection

load_dotenv()

# Map RAWG tag slugs to your perspectives table CHECK constraint values
PERSPECTIVE_TAG_MAPPING = {
    # Direct matches
    "first-person": "First-Person",
    "third-person": "Third-Person",
    "isometric": "Isometric",
    "top-down": "Top Down",
    "text-based": "Text-based",
    "2d": "2D",
    "vr": "Virtual Reality",

    # Derived matches (collapse to parent perspective)
    "third-person-shooter": "Third-Person",
    "2d-fighter": "2D",
    "2d-faiting": "2D",       # Cyrillic variant
    "2d-faiter": "2D",        # Cyrillic variant
    "2d-platformer-3": "2D",
    "2d-platformer-4": "2D",
    "top-down-shooter": "Top Down",

    # Explicitly excluded (do NOT add these):
    # "first-person-mod" -> it's a mod, not the base game perspective
    # "vr-mod"           -> same
    # "bird"             -> irrelevant
}


def get_perspective_id(connection, perspective_name):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT perspective_id FROM perspectives WHERE perspective_name = %s",
        (perspective_name,),
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def import_perspectives():
    connection = get_db_connection()
    if not connection.is_connected():
        print("Failed to connect to DB.")
        return

    # 1. Seed the perspectives table
    cursor = connection.cursor()
    default_perspectives = [
        "First-Person", "Third-Person", "Isometric",
        "2D", "Text-based", "Top Down", "Virtual Reality",
        "2D-HD", "Cockpit View", "Fixed Camera", "Other",
    ]
    for p in default_perspectives:
        cursor.execute(
            "INSERT IGNORE INTO perspectives (perspective_name) VALUES (%s)", (p,)
        )
    connection.commit()

    # 2. Load the JSON
    print("Loading rawg_games.json...")
    try:
        with open("rawg_games.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("Error: rawg_games.json not found.")
        return

    # 3. Map rawg_id -> game_id
    cursor.execute("SELECT rawg_id, game_id FROM games")
    db_games = {str(rawg_id): game_id for rawg_id, game_id in cursor.fetchall()}
    print(f"Loaded {len(db_games)} games from the database.")

    inserted = 0
    matched_tags = 0

    for game in games_data:
        rawg_id = str(game.get("id"))
        if rawg_id not in db_games:
            continue

        game_id = db_games[rawg_id]
        tags = game.get("tags", [])

        for tag in tags:
            slug = tag.get("slug", "").lower()
            mapped = PERSPECTIVE_TAG_MAPPING.get(slug)
            if not mapped:
                continue

            perspective_id = get_perspective_id(connection, mapped)
            if not perspective_id:
                continue

            try:
                cursor.execute(
                    """
                    INSERT IGNORE INTO game_perspectives (game_id, perspective_id)
                    VALUES (%s, %s)
                    """,
                    (game_id, perspective_id),
                )
                if cursor.rowcount > 0:
                    inserted += 1
                matched_tags += 1
            except Exception as e:
                print(f"Error linking {game.get('name')} to {mapped}: {e}")

    connection.commit()
    cursor.close()
    connection.close()
    print(f"\nDone! Matched {matched_tags} perspective tags across games.")
    print(f"Inserted {inserted} new rows into game_perspectives.")


if __name__ == "__main__":
    import_perspectives()