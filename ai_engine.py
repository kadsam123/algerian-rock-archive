import json
import os

def load_artists():
    """Reads the raw JSON file from the data folder."""
    file_path = os.path.join("data", "artists.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_context_string(artists_data):
    """
    Converts the artist data into a single text string for the AI.
    """
    if not artists_data:
        return "No artist data found."

    context = "Here is the encyclopedia of Algerian Rock Music:\n\n"
    
    for artist in artists_data:
        context += f"--- BAND PROFILE ---\n"
        context += f"Name: {artist.get('name', 'Unknown')}\n"
        context += f"Genre: {artist.get('genre', 'Unknown')}\n"
        context += f"Origin: {artist.get('origin', 'Unknown')}\n"
        context += f"Bio: {artist.get('bio', 'No bio available')}\n"
        context += f"Famous Tracks: {artist.get('famous_tracks', [])}\n\n"
        
    return context
