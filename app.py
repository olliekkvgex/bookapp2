import streamlit as st
import requests
import json
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image

# --- CONFIGURATION ---
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# --- HELPER: BARCODE DECODER ---
def decode_barcode(image_file):
    img = Image.open(image_file)
    img_array = np.array(img)
    detected_barcodes = decode(img_array)
    if not detected_barcodes:
        return None
    for barcode in detected_barcodes:
        isbn_data = barcode.data.decode("utf-8")
        if isbn_data:
            return isbn_data
    return None

# --- APP SETUP ---
# Move set_page_config to the very top to avoid errors
st.set_page_config(page_title="ANUBIS - Book Detective", page_icon="Anubis.png")

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Genre Detective", "About Us"])

# --- APP SESSION STATE ---
if "custom_categories" not in st.session_state:
    st.session_state.custom_categories = [
        {"name": "Missing Folk", "desc": "Stories involving disappearances and the search for people."},
        {"name": "Messed Up Families", "desc": "Focuses on complex, toxic, or dramatic family secrets."}
    ]

# --- SIDEBAR: GENRE MANAGER ---
with st.sidebar:
    st.image("logo.png")
    st.header("🛠️ Bespoke Genre Builder")
    
    with st.form("new_genre_form", clear_on_submit=True):
        new_name = st.text_input("Genre Name")
        new_desc = st.text_area("Description")
        if st.form_submit_button("Add to List") and new_name and new_desc:
            st.session_state.custom_categories.append({"name": new_name, "desc": new_desc})
            st.rerun()

    st.write("---")
    st.subheader("💾 Save & Load")
    
    genre_data = json.dumps(st.session_state.custom_categories)
    st.download_button(
        label="Download My Genres",
        data=genre_data,
        file_name="my_bespoke_genres.json",
        mime="application/json",
        help="Saves your current list to your computer."
    )
    
    uploaded_file = st.file_uploader("Upload Saved Genres", type="json")
    if uploaded_file is not None:
        try:
            st.session_state.custom_categories = json.load(uploaded_file)
            st.success("Genres Loaded!")
        except:
            st.error("Invalid file format.")

    if st.button("🗑️ Clear All & Reset"):
        st.session_state.custom_categories = []
        st.rerun()

    st.write("---")
    st.write("**Current Custom Genres:**")
    for cat in st.session_state.custom_categories:
        st.caption(f"• **{cat['name']}**")

# --- PAGE 1: THE MAIN APP ---
if page == "Genre Detective":
    st.image("logo.png", width=150)
    st.title("ANUBIS - Book Detective")

    # --- STEP 1: ISBN INPUT (SCAN OR TYPE) ---
    st.subheader("🔍 Find Your Book")
    tab1, tab2 = st.tabs(["📸 Scan Barcode", "⌨️ Type ISBN"])
    
    scanned_isbn = None
    with tab1:
        img_file = st.camera_input("Point camera at the barcode")
        if img_file:
            with st.spinner("Decoding..."):
                scanned_isbn = decode_barcode(img_file)
                if scanned_isbn:
                    st.success(f"Barcode Found: {scanned_isbn}")
                else:
                    st.error("No barcode detected. Try better lighting or hold it closer.")

    with tab2:
        typed_isbn = st.text_input("Enter ISBN-13:", placeholder="9780141036144")

    # Logic to decide which ISBN to use
    raw_isbn = scanned_isbn if scanned_isbn else typed_isbn
    isbn = raw_isbn.replace("-", "").replace(" ", "").strip() if raw_isbn else ""

    if isbn:
        with st.spinner("🔍 Fetching book data..."):
            ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            res = requests.get(ol_url).json()
            book_key = f"ISBN:{isbn}"
        
        if book_key in res:
            book_data = res[book_key]
            title = book_data.get('title', 'Unknown Title')
            
            raw_subjects = book_data.get('subjects', [])
            subject_names = [s.get('name') if isinstance(s, dict) else str(s) for s in raw_subjects]
            clean_subjects = ", ".join(subject_names[:10])
            
            st.success(f"📖 Found: **{title}**")
            if 'cover' in book_data:
                st.image(book_data['cover'].get('medium', ''), width=150)

            # --- STEP 2: PARSED AI CLASSIFICATION ---
            st.markdown("---")
            if not st.session_state.custom_categories:
                st.warning("Please add custom genres in the sidebar.")
            else:
                with st.spinner("🧠 Categorizing..."):
                    genre_guide = "\n".join([f"- {c['name']}: {c['desc']}" for c in st.session_state.custom_categories])
                    
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                    data = {
                        "model": MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": f"Use ONLY these custom genres: \n{genre_guide}"},
                            {"role": "user", "content": f"Book: {title}. Themes: {clean_subjects}. \n\nRespond ONLY in this exact format: \nPRIMARY: [Genre Name] \nSECONDARY: [Genre Name] \nWHY: [Reasoning]"}
                        ],
                        "temperature": 0.1
                    }
                    
                    response = requests.post(API_URL, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        output = response.json()['choices'][0]['message']['content']
                        lines = output.strip().split("\n")
                        for line in lines:
                            if ":" in line:
                                label, content = line.split(":", 1)
                                st.subheader(label.strip())
                                st.write(content.strip())
                    else:
                        st.error(f"AI Error ({response.status_code})")
        else:
            st.error(f"ISBN {isbn} not found.")

# --- PAGE 2: ABOUT US ---
elif page == "About Us":
    st.title("📖 About Anubis")
    st.image("logo.png", width=100)
    
    st.markdown("""
    ### Our Mission
    Traditional book genres are often too broad. **Anubis** was built to give readers the power to define their own hyper-specific categories and to 
    instantly see where a book fits.
    
    ### How it Works
    1. **Define:** Create your own bespoke genres in the sidebar.
    2. **Scan/Enter:** Use your camera to scan a barcode or enter an ISBN manually.
    3. **Categorise:** Anubis analyses the book's themes against your specific definitions using Llama 3.1 AI.
    
    ### Privacy
    We don't store your data. Your custom genres belong to you—use the **Download** feature 
    to keep your library profiles on your own device.
    """)

st.markdown("---")
st.caption("DEMO | v0.1.1")