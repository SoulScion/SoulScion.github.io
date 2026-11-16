
import json

with open("rawg_games.json", encoding="utf-8") as file:
    games = json.load(file)

print("Total games:", len(games))

fields = [
    "name",
    "released",
    "developers",
    "publishers",
    "genres",
    "platforms"
]

for field in fields:
    populated = sum(
        1 for game in games
        if game.get(field)
    )

    print(f"{field}: {populated}/{len(games)}")