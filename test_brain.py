import os
from ai_engine import load_artists, create_vector_db

print("--- STARTING TEST ---")

# --- PASTE YOUR KEY BELOW ---
# Replace the text inside the quotes with your real AIza... key
os.environ["GOOGLE_API_KEY"] = "AIzaSyClYvVCohsCwxmaqPFK2BrjizY9H3pubZE"

print("\n... Step 1: Loading Artists ...")
try:
    artists = load_artists()
    print(f"✅ Success! Found {len(artists)} artists in the database.")
except Exception as e:
    print(f"❌ Error loading artists: {e}")
    exit()

print("\n... Step 2: Testing Google Connection ...")
try:
    vector_db = create_vector_db(artists)
    print("✅ Success! Google Gemini successfully created the index.")
    print("The brain is ready.")
except Exception as e:
    print(f"❌ Error connecting to Google: {e}")