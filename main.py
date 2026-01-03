import streamlit as st
import google.generativeai as genai
import sqlite3
import os
from PIL import Image

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Algerian Rock Archive (SQL)", layout="wide")
DB_FILE = os.path.join("data", "rock_archive.db")
IMG_FOLDER = "images"

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

# --- 2. DATABASE FUNCTIONS (The New Brain) ---
def get_db_connection():
    """Connects to SQLite and allows accessing columns by name."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Crucial: Lets us use row['name'] like JSON!
    return conn

def load_artists():
    """Fetches all bands from the database."""
    conn = get_db_connection()
    artists = conn.execute("SELECT * FROM artists").fetchall()
    conn.close()
    # Convert to a list of real dictionaries so the UI logic works
    return [dict(row) for row in artists]

def add_artist(artist_data):
    """Inserts a new band into the database."""
    try:
        conn = get_db_connection()
        # Convert list of tracks back to string "Track1, Track2"
        tracks_str = ", ".join(artist_data['famous_tracks'])
        
        conn.execute('''
            INSERT INTO artists (name, genre, origin, era, bio, famous_tracks, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            artist_data['name'], 
            artist_data['genre'], 
            artist_data['origin'], 
            artist_data['era'], 
            artist_data['bio'], 
            tracks_str, 
            artist_data['image']
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def save_image(uploaded_file, artist_name):
    if uploaded_file is None:
        return None
    safe_name = artist_name.replace(" ", "_") + os.path.splitext(uploaded_file.name)[1]
    save_path = os.path.join(IMG_FOLDER, safe_name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return safe_name

def ask_gemini(api_key, context, question, current_focus=None):
    if not api_key:
        return "⚠️ Please enter your Google API Key in the sidebar."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_instruction = f"You are an expert Historian on Algerian Rock Music. Base your answers on this archive:\n{context}"
        
        if current_focus:
            prompt = f"{system_instruction}\n\nUSER FOCUS: The user is currently looking at the profile of '{current_focus}'.\nQUESTION: {question}"
        else:
            prompt = f"{system_instruction}\n\nQUESTION: {question}"
            
        return model.generate_content(prompt).text
    except Exception as e:
        return f"AI Error: {e}"

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Control Panel (SQL Edition)")
    api_key = st.text_input("Google API Key", type="password")
    st.markdown("---")
    app_mode = st.radio("Select Mode:", ["🎸 Visual Shelf", "✍️ Curator (Add Band)"])

# --- 4. PREPARE CONTEXT ---
# We load the data fresh from the DB on every reload
artists_data = load_artists()
# Convert the list of dicts to a string for the AI
global_context = str(artists_data)

# --- 5. MODE A: CURATOR ---
if app_mode == "✍️ Curator (Add Band)":
    st.title("✍️ Curator Station (Database)")
    with st.form("new_artist_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Band Name")
            genre = st.text_input("Genre")
            origin = st.text_input("City")
            era = st.text_input("Active Era")
        with col2:
            bio = st.text_area("Biography")
            tracks = st.text_input("Famous Tracks (comma separated)")
            uploaded_img = st.file_uploader("Upload Album Cover", type=['png', 'jpg', 'jpeg'])
            
        if st.form_submit_button("💾 Save to Database"):
            if not name:
                st.warning("Name is required!")
            else:
                img_filename = save_image(uploaded_img, name)
                new_entry = {
                    "name": name, "genre": genre, "origin": origin, 
                    "era": era, "bio": bio, 
                    "famous_tracks": [t.strip() for t in tracks.split(',')],
                    "image": img_filename
                }
                
                if add_artist(new_entry):
                    st.success(f"✅ {name} committed to SQL Database!")
                    st.balloons()

# --- 6. MODE B: VISUAL SHELF ---
else:
    st.title("🇩🇿 The Algerian Rock Archive")

    if 'selected_artist' not in st.session_state:
        st.session_state.selected_artist = None

    # === GRID VIEW ===
    if st.session_state.selected_artist is None:
        st.subheader("The Collection")
        cols = st.columns(4)
        for index, artist in enumerate(artists_data):
            with cols[index % 4]:
                with st.container(border=True):
                    img_path = artist.get('image')
                    if img_path and os.path.exists(os.path.join(IMG_FOLDER, img_path)):
                        st.image(os.path.join(IMG_FOLDER, img_path), use_container_width=True)
                    else:
                        st.image("https://placehold.co/400x400/202020/FFFFFF/png?text=Vinyl", use_container_width=True)
                    st.markdown(f"**{artist['name']}**")
                    if st.button(f"Explore", key=f"btn_{index}"):
                        st.session_state.selected_artist = artist
                        st.rerun()
        
        st.markdown("---")
        st.subheader("💬 Ask the Historian")
        if prompt := st.chat_input("Ask about the whole era..."):
            with st.chat_message("assistant"):
                st.write(ask_gemini(api_key, global_context, prompt))

    # === DETAIL VIEW ===
    else:
        if st.button("⬅️ Back to Shelf"):
            st.session_state.selected_artist = None
            st.rerun()
            
        artist = st.session_state.selected_artist
        col1, col2 = st.columns([1, 2])
        with col1:
            img_path = artist.get('image')
            if img_path and os.path.exists(os.path.join(IMG_FOLDER, img_path)):
                st.image(os.path.join(IMG_FOLDER, img_path))
            else:
                st.image("https://placehold.co/400x400/202020/FFFFFF/png?text=Vinyl")
            st.info(f"📍 {artist['origin']}")

        with col2:
            st.header(artist['name'])
            st.write(artist['bio'])
            st.subheader("Essential Tracks")
            # In DB, tracks are "Track1, Track2". We split them back to list for display.
            track_list = artist['famous_tracks'].split(',') if isinstance(artist['famous_tracks'], str) else []
            for t in track_list:
                st.markdown(f"🎵 {t}")

        st.markdown("---")
        st.subheader(f"💬 Chat about {artist['name']}")
        if prompt := st.chat_input(f"Ask about {artist['name']}..."):
            with st.chat_message("assistant"):
                st.write(ask_gemini(api_key, global_context, prompt, current_focus=artist['name']))