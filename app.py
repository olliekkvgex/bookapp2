import streamlit as st
import requests
import json
import os

# --- CONFIGURATION ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# --- APP SETUP ---
st.set_page_config(page_title="ANUBIS - Book Detective", page_icon="Anubis.png")

# --- NAVIGATION ---
page = st.sidebar.segmented_control(
    "Navigation", 
    ["Genre Detective", "About Us", "Contact"], 
    default="Genre Detective"
)

# --- APP SESSION STATE ---
if "custom_categories" not in st.session_state:
    st.session_state.custom_categories = [
        {"name": "Missing Folk", "desc": "Stories involving disappearances and the search for people."},
        {"name": "Messed Up Families", "desc": "Focuses on complex, toxic, or dramatic family secrets."}
    ]

# --- SIDEBAR: GENRE MANAGER ---
with st.sidebar:
    st.image("logo.png")
    st.header("🛠️ Genre Settings")

    # --- GENRE PACK LOADER ---
    st.subheader("📚 Genre Packs")
    
    packs = {
        "Manual Mode": None,
        "Thrillers (Pack 1)": "thriller-pack-1.json",
        "Romance (Pack 1)": "romance-pack-1.json"
    }
    
    selected_name = st.selectbox("Choose a Pack:", list(packs.keys()))
    
    if st.button("Apply Pack"):
        pack_filename = packs[selected_name]
        if pack_filename:
            if os.path.exists(pack_filename):
                try:
                    with open(pack_filename, "r") as f:
                        data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
                        st.session_state.custom_categories = data
                        st.success(f"✅ {selected_name} loaded successfully!")
                    else:
                        st.error("JSON format error: Needs 'name' and 'desc' keys.")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
            else:
                st.error(f"File '{pack_filename}' not found.")
        else:
            st.info("Manual Mode active.")

    st.write("---")
    st.header("➕ Add Bespoke Genre")
    with st.form("new_genre_form", clear_on_submit=True):
        new_name = st.text_input("Genre Name")
        new_desc = st.text_area("Description")
        if st.form_submit_button("Add to List") and new_name and new_desc:
            st.session_state.custom_categories.append({"name": new_name, "desc": new_desc})
            st.rerun()

    if st.button("🗑️ Clear All & Reset"):
        st.session_state.custom_categories = []
        st.rerun()

    st.write("---")
    st.write("**Active Genres:**")
    for cat in st.session_state.custom_categories:
        st.caption(f"• **{cat['name']}**")

# --- PAGE 1: GENRE DETECTIVE ---
if page == "Genre Detective":
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image("logo.png", width=80)
    with col_b:
        st.title("ANUBIS - Book Detective")

    raw_isbn = st.text_input("Enter ISBN-13:", placeholder="9780141036144")
    isbn = raw_isbn.replace("-", "").replace(" ", "").strip()

    if isbn:
        with st.spinner("🔍 Gathering intelligence..."):
            ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            res = requests.get(ol_url).json()
            book_key = f"ISBN:{isbn}"
        
        if book_key in res:
            book_data = res[book_key]
            
            # Metadata Extraction
            title = book_data.get('title', 'Unknown Title')
            authors = book_data.get('authors', [])
            author_name = authors[0].get('name') if authors else "Unknown Author"
            raw_subjects = book_data.get('subjects', [])
            subject_names = [s.get('name') if isinstance(s, dict) else str(s) for s in raw_subjects]
            clean_subjects = ", ".join(subject_names[:12])
            notes = book_data.get('notes', "")

            st.markdown("---")
            display_col1, display_col2 = st.columns([1, 2])
            
            with display_col1:
                if 'cover' in book_data:
                    st.image(book_data['cover'].get('large', ''), use_container_width=True)
                else:
                    st.info("No cover available.")
            
            with display_col2:
                st.subheader(title)
                st.write(f"✍️ **Author:** {author_name}")
                st.caption(f"🏷️ **Tags:** {clean_subjects}")
                
                if not st.session_state.custom_categories:
                    st.warning("Please load a pack in the sidebar.")
                else:
                    with st.spinner("🧠 Analyzing..."):
                        try:
                            genre_guide = "\n".join([f"GENRE: {c['name']}\nDEF: {c['desc']}" for c in st.session_state.custom_categories])
                            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                            
                            system_message = f"""You are a professional Book Archivist. 
                            Classify ONLY using these definitions:
                            {genre_guide}"""

                            user_prompt = f"""BOOK: {title}\nAUTHOR: {author_name}\nTHEMES: {clean_subjects}\nNOTES: {notes}
                            Format:
                            PRIMARY: [Genre]
                            SECONDARY: [Genre]
                            WHY: [Two sentences max]"""

                            data = {
                                "model": MODEL_NAME,
                                "messages": [
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": user_prompt}
                                ],
                                "temperature": 0.1
                            }
                            response = requests.post(API_URL, headers=headers, json=data)
                            if response.status_code == 200:
                                st.info(response.json()['choices'][0]['message']['content'])
                            else:
                                st.error(f"AI Error ({response.status_code})")
                        except Exception as e:
                            st.error(f"Classification failed: {e}")
        else:
            st.error(f"ISBN {isbn} not found.")

# --- PAGE 2: ABOUT US ---
elif page == "About Us":
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logo.png", width=100)
    with col2:
        st.title("About Anubis")
    
    st.markdown("""
    ### Our Mission
    Traditional book genres are often too broad. **Anubis** was built to give readers the power to define their own hyper-specific categories.
    
    ### How it Works
    1. **Define:** Create your own bespoke genres or load a **Genre Pack** in the sidebar.
    2. **Analyze:** Enter an ISBN to fetch data via the *Open Library API*.
    3. **Categorise:** Anubis analyses book data against your **custom definitions** using Llama 3.1 AI.
    """)

# --- PAGE 3: CONTACT ---
elif page == "Contact":
    st.title("✉️ Contact Us")
    st.write("Fill out the form below and we will be in touch shortly!")
    
    contact_email = st.secrets["CONTACT_EMAIL"]
    
    contact_form = f"""
    <form action="https://formsubmit.co/{contact_email}" method="POST">
        <input type="text" name="name" placeholder="Full Name" style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;" required>
        <input type="email" name="email" placeholder="Email Address" style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;" required>
        <textarea name="message" placeholder="Your Message" style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc; height: 100px;" required></textarea>
        <button type="submit" style="background-color: #FF4B4B; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Send Submission</button>
    </form>
    """
    st.markdown(contact_form, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("ANUBIS | DEMO v0.1.1")
