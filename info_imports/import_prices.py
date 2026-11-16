import os
import re
import requests
import warnings
from thefuzz import process, fuzz
from dotenv import load_dotenv
from info_imports.collect_rawg import get_db_connection

load_dotenv()
warnings.filterwarnings("ignore", module="thefuzz")

STEAM_JSON_URL = "https://raw.githubusercontent.com/Ephellon/game-store-catalog/main/steam/!.json"


def fetch_steam_catalog():
    print("Downloading Steam catalog from GitHub...")
    response = requests.get(STEAM_JSON_URL, timeout=60)
    response.raise_for_status()
    data = response.json()
    return {entry[0]: entry[1] for entry in data if len(entry) == 2}


def categorize_price(price_str):
    """
    Returns (price_type, numeric_price).
    numeric_price is None for Free/Unavailable/Trial/Announced.
    """
    if not price_str or not isinstance(price_str, str):
        return ("Unknown", None)

    clean = price_str.strip().lower()

    status_map = {
        "free": "Free",
        "unavailable": "Unavailable",
        "announced": "Announced",
        "early access trial": "Trial",
        "game trial": "Trial",
    }

    if clean in status_map:
        return (status_map[clean], None)

    match = re.search(r"[\d,]+\.\d{2}", price_str)
    if match:
        try:
            value = float(match.group().replace(",", ""))
            return ("Standard", value)
        except ValueError:
            return ("Unknown", None)

    return ("Unknown", None)


def digits_signature(title):
    """Returns the tuple of digit-runs in a title, e.g. 'Mafia II' -> ('II',)."""
    return tuple(re.findall(r"\d+", title))


def get_or_create_steam_platform(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT platform_id FROM platforms WHERE platform_name = 'PC (Steam)'")
    result = cursor.fetchone()
    if result:
        cursor.close()
        return result[0]

    cursor.execute("""
        INSERT INTO platforms (rawg_platforms_id, platform_name, type)
        VALUES (NULL, 'PC (Steam)', 'PC')
    """)
    connection.commit()
    platform_id = cursor.lastrowid
    cursor.close()
    return platform_id


def load_games(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT game_id, title FROM games")
    games = {title: game_id for game_id, title in cursor.fetchall()}
    cursor.close()
    return games


def import_prices():
    connection = get_db_connection()
    if not connection.is_connected():
        print("Failed to connect to DB.")
        return

    steam_platform_id = get_or_create_steam_platform(connection)
    print(f"Steam Platform ID: {steam_platform_id}")

    db_games = load_games(connection)
    if not db_games:
        print("No games in the database. Run import_to_db.py first.")
        return

    print(f"Loaded {len(db_games)} games from the database.")

    steam_catalog = fetch_steam_catalog()
    print(f"Loaded {len(steam_catalog)} games from the Steam catalog.")

    db_titles = list(db_games.keys())
    cursor = connection.cursor()

    matched = 0
    inserted = 0
    skipped_free = 0

    for steam_name, steam_data in steam_catalog.items():
        best_match = process.extractOne(steam_name, db_titles, scorer=fuzz.token_sort_ratio)
        if not best_match:
            continue

        match_title, score = best_match[0], best_match[1]
        if score < 90:
            continue

        # Reject sequel mismatches (Jackbox 6 != Jackbox 8, etc.)
        if digits_signature(steam_name) != digits_signature(match_title):
            continue

        game_id = db_games[match_title]

        price_type, numeric_price = categorize_price(steam_data.get("price"))
        if price_type == "Unknown":
            continue

        website_link = steam_data.get("href", "")

        try:
            # 1. Always record the current price (numeric OR status)
            cursor.execute("""
                INSERT INTO prices (game_id, platform_id, regular_price, price_type)
                VALUES (%s, %s, %s, %s)
            """, (game_id, steam_platform_id, numeric_price, price_type))

            # 2. Record a deal only if there is a real numeric price
            if numeric_price is not None:
                cursor.execute("""
                    INSERT INTO deal_prices (game_id, dlc_id, lowest_price, website_link)
                    VALUES (%s, NULL, %s, %s)
                """, (game_id, numeric_price, website_link))
            else:
                skipped_free += 1

            matched += 1
            inserted += 1
            if inserted % 50 == 0:
                print(f"  Inserted {inserted} price records so far...")
                connection.commit()

        except Exception as e:
            print(f"  [!] Error for '{steam_name}' -> '{match_title}': {e}")
            connection.rollback()

    connection.commit()
    cursor.close()
    connection.close()
    print(f"\nDone! Matched {matched} games, inserted {inserted} price rows.")
    print(f"Free/Unavailable games without a deal record: {skipped_free}")


if __name__ == "__main__":
    import_prices()