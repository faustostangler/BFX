import sqlite3
import re
from pathlib import Path

def get_playlist_data(playlist_file):
    playlists = []
    current_genre = None
    with open(playlist_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith('http'):
                playlists.append({'genre': current_genre, 'url': line})
            else:
                current_genre = line
    return playlists

def get_last_tracks(db_path, count=100):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, genre FROM track_info ORDER BY rowid DESC LIMIT ?;", (count,))
    rows = cursor.fetchall()
    conn.close()
    return rows

playlist_file = 'playlist.txt'
db_path = 'data/playlist.db'

if not Path(db_path).exists():
    print("DB not found")
    exit()

playlists = get_playlist_data(playlist_file)
last_tracks = get_last_tracks(db_path)

print(f"Last {len(last_tracks)} tracks in DB:")
track_urls = [t[0] for t in last_tracks]

# We need to find which playlist URL contains these tracks.
# Since we don't have the mapping in the DB, we have to guess or use the genre.

for track_url, title, genre in last_tracks:
    # Try to find a playlist in the same genre
    matching_playlists = [p for p in playlists if p['genre'] == genre]
    print(f"Track: {title} | Genre: {genre} | URL: {track_url}")
    # (In a real scenario, we'd need to fetch playlist items to be 100% sure)
    # But let's just see the unique genres in the last tracks.

unique_genres = []
for t in last_tracks:
    if t[2] not in unique_genres:
        unique_genres.append(t[2])

print(f"\nUnique genres in last {len(last_tracks)} tracks: {unique_genres}")
