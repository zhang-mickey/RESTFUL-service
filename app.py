from flask import Flask, url_for, request, render_template, redirect
import string
import sqlite3
import random
import re

app = Flask(__name__)

DB_FILE = "urls.db"

# Regex for URL validation
URL_REGEX = re.compile(
    r"^(https?://)?"  # Optional http:// or https://
    r"([a-zA-Z0-9.-]+)"  # Domain (e.g., example.com)
    r"(\.[a-zA-Z]{2,})"  # TLD (e.g., .com, .org)
    r"(:\d{1,5})?"  # Optional port
    r"(/.*)?$"  # Optional path/query params
)

# Ensure database exists
def init_db():
    conn = sqlite3.connect(DB_FILE)
    db = conn.cursor()
    db.execute(
        """CREATE TABLE IF NOT EXISTS urls
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    conn.commit()
    conn.close()

init_db()  # Initialize database at startup

# Function to get a new database connection
def get_db():
    conn = sqlite3.connect(DB_FILE)
    return conn, conn.cursor()

# Generate a short URL ensuring uniqueness
def generate_short_url():
    characters = string.ascii_letters + string.digits
    while True:
        short_url = "".join(random.choice(characters) for _ in range(6))
        conn, db = get_db()
        db.execute("SELECT 1 FROM urls WHERE short_url=?", (short_url,))
        if not db.fetchone():  # Ensure it doesn't already exist
            conn.close()
            return short_url
        conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form["original_url"]

        # Validate URL
        if not URL_REGEX.match(original_url):
            return render_template("index.html", error="Invalid URL format.")

        conn, db = get_db()

        # Check if the URL is already shortened
        db.execute("SELECT short_url FROM urls WHERE original_url=?", (original_url,))
        result = db.fetchone()

        if result:
            short_url = result[0]  # Return existing short URL
        else:
            short_url = generate_short_url()
            db.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
            conn.commit()

        conn.close()
        return render_template("index.html", short_url=short_url)

    return render_template("index.html")

@app.route("/<short_url>")
def redirect_to_url(short_url):
    conn, db = get_db()
    db.execute("SELECT original_url FROM urls WHERE short_url=?", (short_url,))
    result = db.fetchone()
    conn.close()

    if result:
        return redirect(result[0])

    return render_template("index.html", error="Short URL not found.")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)