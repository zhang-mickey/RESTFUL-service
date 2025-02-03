from flask import Flask, request, redirect, jsonify, render_template
import sqlite3
import hashlib
import string
import random
import base64
import validators

app = Flask(__name__)
DB_FILE = "urls.db"


# Function to get database connection
def get_db():
    conn = sqlite3.connect(DB_FILE,timeout=10)
    conn.execute('PRAGMA locking_mode = EXCLUSIVE')  # Exclusive locking mode
    conn.row_factory = sqlite3.Row  # Allows us to fetch results as dictionaries
    return conn, conn.cursor()


# Create table
def create_table():
    conn, db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


create_table()


# Function to encode URL using SHA256 + Base62
def generate_short_url(url):
    hash_object = hashlib.sha256(url.encode())
    hash_hex = hash_object.digest()  # Get binary hash
    hash_b64 = base64.urlsafe_b64encode(hash_hex).decode()[:6]  # Take first 6 chars
    return hash_b64


# Function to validate URL
def is_valid_url(url):
    return validators.url(url)


@app.route("/", methods=["GET", "POST", "DELETE"])
def index():
    conn, db = get_db()

    # GET all stored URLs
    if request.method == "GET":
        db.execute("SELECT id, original_url FROM urls ORDER BY created_at DESC")
        urls = db.fetchall()
        conn.close()
        return jsonify([{"id": row["id"], "url": row["original_url"]} for row in urls]), 200

    # DELETE all stored URLs
    if request.method == "DELETE":
        db.execute("DELETE FROM urls")
        conn.commit()
        conn.close()
        return "", 204  # Successfully deleted

    # POST (shorten URL)
    if request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing URL"}), 400

        original_url = data["value"].strip()

        if not is_valid_url(original_url):
            return jsonify({"error": "Invalid URL"}), 400

        short_url = generate_short_url(original_url)

        # Store only if not already present
        db.execute("INSERT OR IGNORE INTO urls (id, original_url) VALUES (?, ?)", (short_url, original_url))
        conn.commit()
        conn.close()

        return jsonify({"id": short_url}), 201


@app.route("/<short_id>", methods=["GET", "PUT", "DELETE"])
def handle_short_url(short_id):
    conn, db = get_db()

    # GET: Redirect to original URL
    if request.method == "GET":
        db.execute("SELECT original_url FROM urls WHERE id = ?", (short_id,))
        result = db.fetchone()
        if result:
            return jsonify({"value": result["original_url"]}), 301
        return "", 404

    # PUT: Update URL
    if request.method == "PUT":
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "Missing URL"}), 400

        new_url = data["url"].strip()
        if not is_valid_url(new_url):
            return jsonify({"error": "Invalid URL"}), 400

        db.execute("UPDATE urls SET original_url = ? WHERE id = ?", (new_url, short_id))
        if db.rowcount == 0:
            return "", 404  # ID not found
        conn.commit()
        conn.close()
        return "", 200

    # DELETE: Remove short URL
    if request.method == "DELETE":
        db.execute("DELETE FROM urls WHERE id = ?", (short_id,))
        if db.rowcount == 0:
            return "", 404  # ID not found
        conn.commit()
        conn.close()
        return "", 204

@app.route("/history")
def history():
    conn, db = get_db()
    db.execute("SELECT original_url, short_url, created_at FROM urls ORDER BY created_at DESC")
    results = db.fetchall()  # Fetch all records from the database
    conn.close()

    return render_template("history.html", results=results)  # Pass 'results' to template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)


# from flask import Flask, url_for, request, render_template, redirect
# import string
# import sqlite3
# import random
# import re
# import base64
# import hashlib
#
# app = Flask(__name__)
#
# DB_FILE = "urls.db"
#
# # Regex for URL validation
# URL_REGEX = re.compile(
#     r"^(https?://)?"  # Optional http:// or https://
#     r"([a-zA-Z0-9.-]+)"  # Domain (e.g., example.com)
#     r"(\.[a-zA-Z]{2,})"  # TLD (e.g., .com, .org)
#     r"(:\d{1,5})?"  # Optional port
#     r"(/.*)?$"  # Optional path/query params
# )
#
# # Ensure database exists
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     db = conn.cursor()
#     db.execute(
#         """CREATE TABLE IF NOT EXISTS urls
#                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 original_url TEXT NOT NULL,
#                 short_url TEXT UNIQUE NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
#     )
#     conn.commit()
#     conn.close()
#
# init_db()  # Initialize database at startup
#
# # Function to get a new database connection
# def get_db():
#     conn = sqlite3.connect(DB_FILE)
#     return conn, conn.cursor()
#
#
# # def generate_short_url():
# #     characters = string.ascii_letters + string.digits
# #     while True:
# #         short_url = "".join(random.choice(characters) for _ in range(6))
# #
# #         # ensure uniqueness
# #         conn, db = get_db()
# #         db.execute("SELECT 1 FROM urls WHERE short_url=?", (short_url,))
# #         if not db.fetchone():  # Ensure it doesn't already exist
# #             conn.close()
# #             return short_url
# #         conn.close()
#
# # Generate a short URL using SHA256 + Base62
# def generate_short_url(original_url):
#     url_hash = hashlib.sha256(original_url.encode()).digest()  # Hash the URL
#     base62_encoded = base64.urlsafe_b64encode(url_hash).decode().rstrip("=")  # Base62 encoding
#     short_url = base62_encoded[:6]  # Take the first 6 characters
#
#     conn, db = get_db()
#
#     # Check for collisions
#     attempt = 1
#     while True:
#         db.execute("SELECT original_url FROM urls WHERE short_url=?", (short_url,))
#         if not db.fetchone():  # If not found, it's unique
#             break
#         # Collision detected: Try a longer substring
#         short_url = base62_encoded[:6 + attempt]
#         attempt += 1
#         if attempt > 10:  # If too many attempts, use a random suffix
#             short_url += base64.urlsafe_b64encode(hashlib.md5(original_url.encode()).digest()).decode()[:2]
#             break
#
#     conn.close()
#     return short_url
#
#

# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         original_url = request.form["original_url"]
#
#         # Validate URL
#         if not URL_REGEX.match(original_url):
#             return render_template("index.html", error="Invalid URL format.")
#
#         conn, db = get_db()
#
#         # Check if the URL is already shortened
#         db.execute("SELECT short_url FROM urls WHERE original_url=?", (original_url,))
#         result = db.fetchone()
#
#         if result:
#             short_url = result[0]  # Return existing short URL
#         else:
#             short_url = generate_short_url(original_url)
#             db.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
#             conn.commit()
#
#         conn.close()
#         return render_template("index.html", short_url=short_url)
#
#     return render_template("index.html")
#
# @app.route("/<short_url>")
# def redirect_to_url(short_url):
#     conn, db = get_db()
#     db.execute("SELECT original_url FROM urls WHERE short_url=?", (short_url,))
#     result = db.fetchone()
#     conn.close()
#
#     if result:
#         return redirect(result[0])
#
#     return render_template("index.html", error="Short URL not found.")
#
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=8080)