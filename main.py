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

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

# --- 2. HELPER FUNCTIONS ---
def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
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
    """Unified AI Function for Global or Specific questions"""
    if not api_key:
        return "⚠️ Please enter your Google API Key in the sidebar."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build the Smart Context
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
    st.header("⚙️ Control Panel")
    api_key = st.text_input("Google API Key", type="password")
    st.markdown("---")
    app_mode = st.radio("Select Mode:", ["🎸 Visual Shelf", "✍️ Curator (Add Band)"])

# --- 4. DATA LOADING ---
artists = load_artists()
global_context = get_context_string(artists) # This string holds the ENTIRE DB

# --- 5. MODE A: CURATOR ---
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
            uploaded_img = st.file_uploader("Upload Album Cover", type=['png', 'jpg', 'jpeg'])
            
        if st.form_submit_button("💾 Save to Archive"):
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
                artists.append(new_entry)
                if save_data(artists):
                    st.success(f"✅ {name} added!")
                    st.balloons()

# --- 6. MODE B: VISUAL SHELF ---
else:
    st.title("🇩🇿 The Algerian Rock Archive")

    if 'selected_artist' not in st.session_state:
        st.session_state.selected_artist = None

    # === VIEW 1: THE GRID (Global View) ===
    if st.session_state.selected_artist is None:
        st.subheader("The Collection")
        cols = st.columns(4)
        for index, artist in enumerate(artists):
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
        # GLOBAL CHAT (New!)
        st.subheader("💬 Ask the Historian (General)")
        if prompt := st.chat_input("Ask about the whole era..."):
            with st.chat_message("assistant"):
                st.write(ask_gemini(api_key, global_context, prompt))

    # === VIEW 2: DETAIL PAGE (Specific View) ===
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
            st.info(f"📍 {artist.get('origin')}")

        with col2:
            st.header(artist['name'])
            st.write(artist.get('bio'))
            st.subheader("Essential Tracks")
            for t in artist.get('famous_tracks', []):
                st.markdown(f"🎵 {t}")

        st.markdown("---")
        # FOCUSED CHAT
        st.subheader(f"💬 Chat about {artist['name']}")
        if prompt := st.chat_input(f"Ask about {artist['name']}..."):
            # We pass the same Global Context, but ADD the current focus name
            with st.chat_message("assistant"):
                st.write(ask_gemini(api_key, global_context, prompt, current_focus=artist['name']))