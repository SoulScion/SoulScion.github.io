from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import mysql.connector
from db_connect import get_db_connection

app = Flask(__name__)

# Allows for a static frontend to call this file
CORS(app)


# Main Page:

def query(sql, params=(), dictionary=True):
    """Run a SELECT and return rows. Raises on DB error."""
    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=dictionary)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()

def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE with commit/rollback."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except mysql.connector.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


# Main Page:

@app.get("/api/games/all")
def all_games():
    rows = query("""
        SELECT 
            g.game_id, 
            g.title, 
            g.earliest_release, 
            p.publisher_name,
            (SELECT d.company_name 
             FROM game_credits gc 
             JOIN developers d ON gc.developer_id = d.developer_id 
             WHERE gc.game_id = g.game_id 
             LIMIT 1) AS developer_name,
            (SELECT pl.platform_name 
             FROM game_availability ga 
             JOIN platforms pl ON ga.platform_id = pl.platform_id 
             WHERE ga.game_id = g.game_id 
             ORDER BY pl.release_date ASC 
             LIMIT 1) AS platform_name
        FROM games g
        LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
        ORDER BY g.game_id ASC
    """)
    return jsonify(rows)


# Searching:

@app.get("/api/games/search")
def search_games():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify({"error": "query parameter 'q' is required"}), 400
    rows = query("""
        SELECT g.game_id, g.title, g.earliest_release, p.publisher_name
        FROM games g
        LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
        WHERE g.title LIKE %s
        ORDER BY g.title
        LIMIT 50
    """, (f"%{term}%",))
    return jsonify(rows)


# Related Data:

@app.get("/api/games/<int:game_id>")
def game_profile(game_id):
    base = query("""
        SELECT g.*, p.publisher_name
        FROM games g
        LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
        WHERE g.game_id = %s
    """, (game_id,))
    if not base:
        abort(404, description="Game not found")
    game = base[0]

    game["developers"] = [r["company_name"] for r in query(
        """SELECT d.company_name FROM game_credits gc
           JOIN developers d ON gc.developer_id = d.developer_id
           WHERE gc.game_id = %s""", (game_id,))]

    game["genres"] = [r["genre_name"] for r in query(
        """SELECT ge.genre_name FROM game_genres gg
           JOIN genres ge ON gg.genre_id = ge.genre_id
           WHERE gg.game_id = %s""", (game_id,))]

    game["platforms"] = query(
        """SELECT pl.platform_name, pl.type FROM game_availability ga
           JOIN platforms pl ON ga.platform_id = pl.platform_id
           WHERE ga.game_id = %s""", (game_id,))

    game["perspectives"] = [r["perspective_name"] for r in query(
        """SELECT pe.perspective_name FROM game_perspectives gp
           JOIN perspectives pe ON gp.perspective_id = pe.perspective_id
           WHERE gp.game_id = %s""", (game_id,))]

    game["socials"] = [r["type_name"] for r in query(
        """SELECT st.type_name FROM game_socials gs
           JOIN social_types st ON gs.type_id = st.type_id
           WHERE gs.game_id = %s""", (game_id,))]

    game["prices"] = query(
        """SELECT pl.platform_name, pr.price_type, pr.regular_price
           FROM prices pr JOIN platforms pl ON pr.platform_id = pl.platform_id
           WHERE pr.game_id = %s""", (game_id,))

    game["dlc_count"] = query(
        "SELECT COUNT(*) AS n FROM dlcs WHERE game_id = %s", (game_id,))[0]["n"]

    return jsonify(game)


# Add Publishers and Developers:

@app.post("/api/publishers")
def add_publisher():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    existing = query(
        "SELECT publisher_id FROM publishers WHERE LOWER(publisher_name) = LOWER(%s)",
        (name,))
    if existing:
        return jsonify({"error": f"Publisher '{name}' already exists"}), 409

    try:
        new_id = execute(
            "INSERT INTO publishers (publisher_name) VALUES (%s)", (name,))
        return jsonify({"publisher_id": new_id, "publisher_name": name}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/developers")
def add_developer():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    existing = query(
        "SELECT developer_id FROM developers WHERE LOWER(company_name) = LOWER(%s)",
        (name,))
    if existing:
        return jsonify({"error": f"Developer '{name}' already exists"}), 409

    try:
        new_id = execute(
            "INSERT INTO developers (company_name) VALUES (%s)", (name,))
        return jsonify({"developer_id": new_id, "company_name": name}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500




# Grabbing and Deleting Publishers:
@app.get("/api/publishers")
def get_publishers():
    # Order by publisher_id DESC so newest additions appear at the top
    rows = query("SELECT publisher_id, publisher_name FROM publishers ORDER BY publisher_id DESC")
    return jsonify(rows)

@app.delete("/api/publishers/<int:publisher_id>")
def delete_publisher(publisher_id):
    try:
        # Foreign key constraints might prevent deletion if a game uses this publisher
        execute("DELETE FROM publishers WHERE publisher_id = %s", (publisher_id,))
        return jsonify({"status": "deleted"})
    except mysql.connector.Error:
        return jsonify({"error": "Cannot delete: This publisher is linked to existing games."}), 409

# Grabbing and Deleting Developers:
@app.get("/api/developers")
def get_developers():
    rows = query("SELECT developer_id, company_name FROM developers ORDER BY developer_id DESC")
    return jsonify(rows)

@app.delete("/api/developers/<int:developer_id>")
def delete_developer(developer_id):
    try:
        execute("DELETE FROM developers WHERE developer_id = %s", (developer_id,))
        return jsonify({"status": "deleted"})
    except mysql.connector.Error:
        return jsonify({"error": "Cannot delete: This developer is linked to existing games."}), 409


# Update the Copies Sold:

@app.patch("/api/games/<int:game_id>/copies")
def update_copies(game_id):
    data = request.get_json(silent=True) or {}
    if "copies_sold" not in data:
        return jsonify({"error": "copies_sold is required"}), 400
    try:
        copies = int(data["copies_sold"])
    except (TypeError, ValueError):
        return jsonify({"error": "copies_sold must be an integer"}), 400
    if copies < 0:
        return jsonify({"error": "copies_sold must be >= 0"}), 400

    if not query("SELECT game_id FROM games WHERE game_id = %s", (game_id,)):
        return jsonify({"error": "Game not found"}), 404

    execute("UPDATE games SET copies_sold = %s WHERE game_id = %s",
            (copies, game_id))
    return jsonify({"game_id": game_id, "copies_sold": copies})


# Summary of Genres by Price:

@app.get("/api/reports/top-genres")
def top_genres():
    rows = query("""
        SELECT ge.genre_name,
               COUNT(DISTINCT g.game_id) AS game_count,
               ROUND(AVG(pr.regular_price), 2) AS avg_price
        FROM genres ge
        JOIN game_genres gg ON ge.genre_id = gg.genre_id
        JOIN games g ON gg.game_id = g.game_id
        JOIN prices pr ON g.game_id = pr.game_id
        WHERE pr.regular_price IS NOT NULL
        GROUP BY ge.genre_name
        HAVING COUNT(DISTINCT g.game_id) >= 3
        ORDER BY avg_price DESC
        LIMIT 15
    """)
    return jsonify(rows)


# Additional - Content Gap Report:

@app.get("/api/reports/no-dlc")
def games_without_dlc():
    rows = query("""
        SELECT 
            g.game_id, 
            g.title, 
            p.publisher_name,
            (SELECT d.company_name 
             FROM game_credits gc 
             JOIN developers d ON gc.developer_id = d.developer_id 
             WHERE gc.game_id = g.game_id 
             LIMIT 1) AS developer_name
        FROM games g
        LEFT JOIN dlcs d ON g.game_id = d.game_id
        LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
        WHERE d.dlc_id IS NULL
        ORDER BY g.title
        LIMIT 50
    """)
    return jsonify(rows)


# Error Handiling:

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)