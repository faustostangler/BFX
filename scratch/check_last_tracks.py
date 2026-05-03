import sqlite3
import os

db_path = "data/playlist.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, genre FROM track_info ORDER BY rowid DESC LIMIT 20;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
else:
    print(f"Database {db_path} not found.")
