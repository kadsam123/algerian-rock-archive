import streamlit as st
import google.generativeai as genai
import json
import os
from PIL import Image
from ai_engine import load_artists, get_context_string

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Algerian Rock Archive", layout="wide")
DATA_FILE = os.path.join("data", "artists.json")
IMG_FOLDER = "images"

# Ensure image folder exists
if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

# --- 2. HELPER FUNCTIONS ---
def save_data(data):
    """Writes the list of artists to the JSON file."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def save_image(uploaded_file, artist_name):
    """Saves an uploaded image using the artist's name."""
    if uploaded_file is None:
        return None
    
    # Create a safe filename (e.g., "Raïna_Raï.jpg")
    safe_name = artist_name.replace(" ", "_") + os.path.splitext(uploaded_file.name)[1]
    save_path = os.path.join(IMG_FOLDER, safe_name)
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return safe_name

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Control Panel")
    api_key = st.text_input("Google API Key", type="password")
    st.markdown("---")
    app_mode = st.radio("Select Mode:", ["🎸 Visual Shelf", "✍️ Curator (Add Band)"])

# --- 4. MODE A: CURATOR (ADD BAND) ---
if app_mode == "✍️ Curator (Add Band)":
    st.title("✍️ Curator Station")
    
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
            # NEW: Image Uploader
            uploaded_img = st.file_uploader("Upload Album Cover", type=['png', 'jpg', 'jpeg'])
            
        submitted = st.form_submit_button("💾 Save to Archive")
        
        if submitted:
            if not name:
                st.warning("Name is required!")
            else:
                # 1. Handle Image
                img_filename = save_image(uploaded_img, name)
                
                # 2. Prepare Data
                new_entry = {
                    "name": name,
                    "genre": genre,
                    "origin": origin,
                    "era": era,
                    "bio": bio,
                    "famous_tracks": [t.strip() for t in tracks.split(',')],
                    "image": img_filename  # Save the filename!
                }
                
                # 3. Load & Append
                artists = load_artists()
                artists.append(new_entry)
                
                if save_data(artists):
                    st.success(f"✅ {name} added to the shelf!")
                    st.balloons()

# --- 5. MODE B: VISUAL SHELF (NETFLIX STYLE) ---
else:
    st.title("🇩🇿 The Algerian Rock Archive")
    artists = load_artists()
    
    # -- STATE MANAGEMENT --
    # If a user clicks a card, we remember which artist they picked
    if 'selected_artist' not in st.session_state:
        st.session_state.selected_artist = None

    # -- VIEW 1: THE GRID (Show this if no artist is selected) --
    if st.session_state.selected_artist is None:
        st.subheader("The Collection")
        
        # Create a grid of 4 columns
        cols = st.columns(4)
        for index, artist in enumerate(artists):
            with cols[index % 4]:
                # Card Container
                with st.container(border=True):
                    # Show Image or Placeholder
                    img_path = artist.get('image')
                    if img_path and os.path.exists(os.path.join(IMG_FOLDER, img_path)):
                        st.image(os.path.join(IMG_FOLDER, img_path), use_container_width=True)
                    else:
                        st.image("https://placehold.co/400x400/202020/FFFFFF/png?text=Vinyl", use_container_width=True)
                    
                    st.markdown(f"**{artist['name']}**")
                    st.caption(artist.get('genre', 'Unknown'))
                    
                    # The "Open" Button
                    if st.button(f"Explore", key=f"btn_{index}"):
                        st.session_state.selected_artist = artist
                        st.rerun()

    # -- VIEW 2: THE DETAIL PAGE (Show this if artist IS selected) --
    else:
        # "Back to Shelf" Button
        if st.button("⬅️ Back to Shelf"):
            st.session_state.selected_artist = None
            st.rerun()
            
        artist = st.session_state.selected_artist
        
        # Layout: Image Left, Text Right
        col1, col2 = st.columns([1, 2])
        with col1:
            img_path = artist.get('image')
            if img_path and os.path.exists(os.path.join(IMG_FOLDER, img_path)):
                st.image(os.path.join(IMG_FOLDER, img_path))
            else:
                st.image("https://placehold.co/400x400/202020/FFFFFF/png?text=Vinyl")
                
            st.info(f"📍 {artist.get('origin')}")
            st.info(f"🎸 {artist.get('genre')}")

        with col2:
            st.header(artist['name'])
            st.write(artist.get('bio'))
            st.subheader("Essential Tracks")
            for t in artist.get('famous_tracks', []):
                st.markdown(f"🎵 {t}")

        st.markdown("---")
        
        # -- AI CHAT (Context-Aware) --
        st.subheader(f"💬 Chat about {artist['name']}")
        if prompt := st.chat_input(f"Ask about {artist['name']}..."):
            if not api_key:
                st.error("Enter API Key in sidebar.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # Focused Prompt
                    full_prompt = f"""
                    Context: {artist}
                    Question: {prompt}
                    """
                    response = model.generate_content(full_prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(e)