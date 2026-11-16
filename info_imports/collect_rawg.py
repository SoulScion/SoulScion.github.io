import os
import requests
import json
import time
import random
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

PLATFORM_TYPE_MAPPING = {
    # PC
    "pc": "PC",

    # Consoles
    "playstation": "Console",
    "playstation2": "Console",
    "playstation3": "Console",
    "playstation4": "Console",
    "playstation5": "Console",
    "xbox": "Console",
    "xbox360": "Console",
    "xbox-one": "Console",
    "xbox-series-x": "Console",
    "nintendo-64": "Console",
    "wii": "Console",
    "gamecube": "Console",

    # Handhelds
    "game-boy": "Handheld",
    "game-boy-advance": "Handheld",
    "3ds": "Handheld",
    "ps-vita": "Handheld",
    "psp": "Handheld",

    # Mobiles
    "ios": "Mobile",
    "android": "Mobile",

    # Hybrid
    "wii-u": "Handheld/Console Hybrid",
    "nintendo-switch": "Handheld/Console Hybrid"
}

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", 3306)), # Adding port is good practice
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}

print("DB_USER:", os.getenv("MYSQL_USER"))
print("DB_PASSWORD:", "***" if os.getenv("MYSQL_PASSWORD") else "EMPTY")

def get_db_connection():
    """Connect to the games_catalog MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def get_existing_game_ids(connection):
    """Return all RAWG game IDs already stored in the database."""
    cursor = connection.cursor()

    cursor.execute("""
        SELECT rawg_id
        FROM games
        WHERE rawg_id IS NOT NULL
    """)

    existing_ids = {row[0] for row in cursor.fetchall()}

    cursor.close()
    return existing_ids

def get_or_insert_publisher(connection, publisher):
    """Find or insert a publisher and return its database ID."""
    cursor = connection.cursor()

    cursor.execute("""
        INSERT IGNORE INTO publishers
            (rawg_publisher_id, publisher_name)
        VALUES (%s, %s)
    """, (publisher["id"], publisher["name"]))

    cursor.execute("""
        SELECT publisher_id
        FROM publishers
        WHERE rawg_publisher_id = %s
    """, (publisher["id"],))

    publisher_id = cursor.fetchone()[0]
    cursor.close()

    return publisher_id


def get_or_insert_developer(connection, developer):
    """Find or insert a developer and return its database ID."""
    cursor = connection.cursor()

    cursor.execute("""
        INSERT IGNORE INTO developers
            (rawg_developers_id, company_name)
        VALUES (%s, %s)
    """, (developer["id"], developer["name"]))

    cursor.execute("""
        SELECT developer_id
        FROM developers
        WHERE rawg_developers_id = %s
    """, (developer["id"],))

    developer_id = cursor.fetchone()[0]
    cursor.close()

    return developer_id


def get_or_insert_genre(connection, genre):
    """Find or insert a genre and return its database ID."""
    cursor = connection.cursor()

    cursor.execute("""
        INSERT IGNORE INTO genres (genre_name)
        VALUES (%s)
    """, (genre["name"],))

    cursor.execute("""
        SELECT genre_id
        FROM genres
        WHERE genre_name = %s
    """, (genre["name"],))

    genre_id = cursor.fetchone()[0]
    cursor.close()

    return genre_id


def get_or_insert_platform(connection, platform):
    """Find or insert a platform and return its database ID."""
    cursor = connection.cursor()

    platform_type = PLATFORM_TYPE_MAPPING.get(platform["slug"])

    cursor.execute("""
        INSERT IGNORE INTO platforms
            (rawg_platforms_id, platform_name, type)
        VALUES (%s, %s, %s)
    """, (platform["id"], platform["name"], platform_type))

    cursor.execute("""
        SELECT platform_id
        FROM platforms
        WHERE rawg_platforms_id = %s
    """, (platform["id"],))

    platform_id = cursor.fetchone()[0]
    cursor.close()

    return platform_id

API_KEY = os.getenv("RAWG_API_KEY")
BASE_URL = "https://api.rawg.io/api"

if not API_KEY:
    raise RuntimeError("RAWG_API_KEY is missing from your .env file")

session = requests.Session()

def rawg_get(endpoint, params=None):
    params = params or {}
    params["key"] = API_KEY

    # We will try up to 4 times if the server gives a 502 error
    for attempt in range(4):
        try:
            response = session.get(
                f"{BASE_URL}/{endpoint.lstrip('/')}",
                params=params,
                timeout=30
            )
            # This will trigger if the status code is 4xx or 5xx (like 502)
            response.raise_for_status() 
            return response.json()
            
        except requests.RequestException as error:
            if attempt == 3: # If it fails on the 4th try, raise the error
                raise error
            print(f"  [!] API hiccup ({error}). Retrying in 3 seconds...")
            time.sleep(3) # Wait 3 seconds before trying again

# Genres to deliberately include in the sample.
# TARGET_GENRES = [
#     "action", "indie", "adventure", "role-playing-games-rpg",
#     "strategy", "shooter", "casual", "simulation",
#     "puzzle", "arcade", "platformer", "racing",
#     "sports", "fighting", "family"
# ]

# # Get RAWG's genre IDs instead of assuming fixed IDs.
# genre_data = rawg_get("genres", {"page_size": 40})


# genre_ids = {
#     genre["slug"]: genre["id"]
#     for genre in genre_data["results"]
# }

# # Collect candidate games from each genre.
# games_by_id = {}

# for genre_slug in TARGET_GENRES:
#     genre_id = genre_ids.get(genre_slug)

#     if genre_id is None:
#         print(f"Genre not found: {genre_slug}")
#         continue

#     print(f"Collecting genre: {genre_slug}")

#     for page in range(1, 4):
#         data = rawg_get("games", {
#             "genres": genre_id,
#             "page": page,
#             "page_size": 40
#         })

#         for game in data.get("results", []):
#             games_by_id[game["id"]] = game

#         time.sleep(0.75)

# # Keep a varied sample, rather than simply taking the first 500.
# candidates = list(games_by_id.values())

# # Shuffle deterministically so the same run gives the same sample.
# import random
# random.Random(42).shuffle(candidates)

# selected = candidates[:500]

# print(f"Collected {len(candidates)} unique candidates.")
# print(f"Selected {len(selected)} games.")

# # Get the full details for each selected game.
# detailed_games = []

# for index, game in enumerate(selected, start=1):
#     try:
#         details = rawg_get(f"games/{game['id']}")
#         detailed_games.append(details)

#         if index % 25 == 0:
#             print(f"Retrieved details for {index}/{len(selected)} games")

#         time.sleep(0.75)

#     except requests.RequestException as error:
#         print(f"Could not retrieve {game['name']}: {error}")

# # Preserve the original API responses.
# with open("rawg_games.json", "w", encoding="utf-8") as file:
#     json.dump(detailed_games, file, indent=2, ensure_ascii=False)

# print(f"Saved {len(detailed_games)} detailed games to rawg_games.json")

# Temp Code:
if __name__ == "__main__":
    # 1. Test the connection
    print("Testing database connection...")
    try:
        connection = get_db_connection()
        if connection.is_connected():
            print("Successfully connected to games_catalog!")
            
            # OPTIONAL: Here is where you would eventually call your import function
            # import_json_to_db(connection, "rawg_games.json")
            
        connection.close()
    except Exception as e:
        print(f"Connection failed: {e}")