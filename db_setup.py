import sqlite3
import json
import os

JSON_FILE = os.path.join("data", "artists.json")
DB_FILE = os.path.join("data", "rock_archive.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            genre TEXT,
            origin TEXT,
            era TEXT,
            bio TEXT,
            famous_tracks TEXT,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("? Database initialized.")

def migrate_data():
    if not os.path.exists(JSON_FILE):
        print("?? No JSON file found. Skipping migration.")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print(f"?? Migrating {len(data)} artists...")
    
    for artist in data:
        tracks_str = ", ".join(artist.get('famous_tracks', []))
        cursor.execute('''
            INSERT INTO artists (name, genre, origin, era, bio, famous_tracks, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (artist['name'], artist.get('genre'), artist.get('origin'), artist.get('era'), artist.get('bio'), tracks_str, artist.get('image')))
        
    conn.commit()
    conn.close()
    print("? Migration complete!")

if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except:
            pass
    init_db()
    migrate_data()
