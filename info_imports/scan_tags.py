import json
from collections import Counter

def scan_tags():
    with open("rawg_games.json", "r", encoding="utf-8") as f:
        games = json.load(f)

    # Keywords to look for in tag slugs/names
    perspective_keywords = [
        "first-person", "third-person", "isometric", 
        "top-down", "fixed-camera", "text-based",
        "2d", "virtual-reality", "vr", "cockpit", "side-view", "bird"
    ]

    tag_counter = Counter()
    
    for game in games:
        tags = game.get("tags", [])
        for tag in tags:
            slug = tag.get("slug", "").lower()
            name = tag.get("name", "").lower()
            
            # Check if any keyword is in the slug or name
            for keyword in perspective_keywords:
                if keyword in slug or keyword in name:
                    tag_counter[f"{name} (slug: {slug})"] += 1
                    break # Count each tag only once per game

    print("Perspective-related tags found in your 500 games:\n")
    for tag, count in tag_counter.most_common():
        print(f"  {count:>4} games  |  {tag}")

if __name__ == "__main__":
    scan_tags()