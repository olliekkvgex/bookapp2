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
    
    # Dictionary mapping friendly names to filenames
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
                    
                    # Validation: Ensure it's a list with 'name' keys
                    if isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
                        st.session_state.custom_categories = data
                        st.success(f"✅ {selected_name} loaded successfully!")
                    else:
                        st.error("JSON format error: Needs 'name' and 'desc' keys.")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
            else:
                st.error(f"File '{pack_filename}' not found in GitHub.")
        else:
            st.info("Manual Mode: Add your own genres below.")

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

# --- PAGE 1: GENRE DETECTIVE (MAIN APP) ---
if page == "Genre Detective":
    st.image("logo.png", width=150)
    st.title("ANUBIS - Book Detective")

    # ISBN Input
    raw_isbn = st.text_input("Enter ISBN-13:", placeholder="9780141036144")
    isbn = raw_isbn.replace("-", "").replace(" ", "").strip()

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

        # --- IMPROVED AI CLASSIFICATION SECTION ---
            st.markdown("---")
            if not st.session_state.custom_categories:
                st.warning("Please load a pack or add genres in the sidebar.")
            else:
                with st.spinner("🧠 Analyzing themes and matching categories..."):
                    try:
                        # Formatting the guide clearly for the AI
                        genre_guide = "\n".join([f"GENRE: {c['name']}\nDESCRIPTION: {c['desc']}\n---" for c in st.session_state.custom_categories])
                        
                        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                        
                        # The "System Message" is now much more strict
                        system_message = f"""You are a professional Book Archivist. 
                        Your task is to classify books based ONLY on the specific Bespoke Genre definitions provided below. 
                        
                        RULES:
                        1. Carefully read the DESCRIPTION of each genre.
                        2. Analyze the book title and themes for subtle clues.
                        3. If a book fits multiple genres, choose the one where the DESCRIPTION most closely matches the primary plot.
                        4. Do not use standard literary genres unless they are in the list provided.
                        
                        BESPOKE GENRE DEFINITIONS:
                        {genre_guide}"""

                        user_prompt = f"""Please classify the following book:
                        TITLE: {title}
                        THEMES/BLURB TAGS: {clean_subjects}
                        
                        Respond in this exact format:
                        PRIMARY: [Insert the Name of the best matching genre]
                        SECONDARY: [Insert the second best match, or 'None']
                        WHY: [A concise 2-sentence explanation of why the book's themes match your chosen genre descriptions]"""

                        data = {
                            "model": MODEL_NAME,
                            "messages": [
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.1 # Low temperature ensures consistent, logical choices
                        }
                        
                        response = requests.post(API_URL, headers=headers, json=data)
                        
                        if response.status_code == 200:
                            output = response.json()['choices'][0]['message']['content']
                            st.markdown(output)
                        else:
                            st.error(f"AI Error ({response.status_code})")
                    except KeyError:
                        st.error("Error building the genre guide. Please ensure your genres have 'name' and 'desc' keys.")
        else:
            st.error(f"ISBN {isbn} not found.")

# --- PAGE 2: ABOUT US ---
elif page == "About Us":
    # Create two columns: one narrow for the logo, one wide for the title
    # Adjust the numbers [1, 4] to change the ratio of widths
    col1, col2 = st.columns([1, 5])

    with col1:
        st.image("logo.png", width=100)

    with col2:
        # We use a header or a title here. 
        # Note: st.title sometimes adds extra padding; st.header might align better.
        st.title("About Anubis")
    
    st.markdown("""
    ### Our Mission
    Traditional book genres are often too broad. **Anubis** was built to give readers the power to define their own hyper-specific categories.
    
    ### How it Works
    1. **Define:** Create your own bespoke genres or load a **Genre Pack** in the sidebar.
    2. **Analyze:** Enter an ISBN to fetch data via the *Open Library API*.
    3. **Categorise:** Anubis analyses book data against your **custom definitions** or our pre-built **Genre Packs** 
    """)

# --- PAGE 3: CONTACT ---
elif page == "Contact":
    st.title("Contact Us")

    st.markdown("""
    ### Get In Touch
    Fill out the form below and we will be in touch with you as soon as we can!""")


# Footer
st.markdown("---")
st.caption("DEMO | v0.1.1")
