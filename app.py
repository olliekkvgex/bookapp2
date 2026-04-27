import streamlit as st
import requests

# --- CONFIGURATION ---
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# --- APP SESSION STATE (The Memory) ---
if "custom_categories" not in st.session_state:
    # Default starter list
    st.session_state.custom_categories = [
        {"name": "Cozy Crime", "desc": "Lighthearted mystery, no gore, usually a small town setting."},
        {"name": "Hard Sci-Fi", "desc": "Focuses on technical accuracy and hard science."}
    ]

# --- SIDEBAR: GENRE MANAGER ---
with st.sidebar:
    st.header("🛠️ Custom Genre Builder")
    st.write("Define your own categories below:")
    
    with st.form("new_genre_form", clear_on_submit=True):
        new_name = st.text_input("Genre Name (e.g. 'Dark Academia')")
        new_desc = st.text_area("Description (What makes a book fit here?)")
        add_btn = st.form_submit_button("Add Genre to List")
        
        if add_btn and new_name and new_desc:
            st.session_state.custom_categories.append({"name": new_name, "desc": new_desc})
            st.success(f"Added {new_name}!")

    if st.button("Reset to Default"):
        st.session_state.custom_categories = []
        st.rerun()

    st.write("---")
    st.write("**Current Bespoke List:**")
    for cat in st.session_state.custom_categories:
        st.caption(f"• **{cat['name']}**: {cat['desc']}")

# --- MAIN APP UI ---
st.set_page_config(page_title="Custom Genre Detective", page_icon="🕵️‍♀️")
st.title("🕵️‍♀️ Bespoke Genre Detective")
st.write("Add your own genres in the sidebar, then enter an ISBN below.")

# --- STEP 1: ISBN INPUT ---
raw_isbn = st.text_input("Enter ISBN-13:")
isbn = raw_isbn.replace("-", "").replace(" ", "").strip()

if isbn:
    # 1. Fetch Book Data
    with st.spinner("🔍 Fetching book..."):
        ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        res = requests.get(ol_url).json()
        book_key = f"ISBN:{isbn}"
    
    if book_key in res:
        book_data = res[book_key]
        title = book_data.get('title', 'Unknown Title')
        
        # Clean subjects
        raw_subjects = book_data.get('subjects', [])
        subject_names = [s.get('name') if isinstance(s, dict) else str(s) for s in raw_subjects]
        clean_subjects = ", ".join(subject_names[:10])
        
        st.success(f"📖 Found: **{title}**")
        if 'cover' in book_data:
            st.image(book_data['cover'].get('medium', ''), width=150)

        # --- STEP 2: CUSTOM AI CLASSIFICATION ---
        st.markdown("---")
        if not st.session_state.custom_categories:
            st.warning("Please add at least one custom genre in the sidebar first!")
        else:
            with st.spinner("🧠 Matching to your bespoke genres..."):
                # Convert the list of dicts into a readable string for the AI
                genre_guide = "\n".join([f"- {c['name']}: {c['desc']}" for c in st.session_state.custom_categories])
                
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                
                data = {
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a librarian. I will give you a list of custom genres and their descriptions. Pick the ONE best match. \n\nGENRE LIST:\n{genre_guide}"
                        },
                        {
                            "role": "user", 
                            "content": f"Book: {title}. Themes: {clean_subjects}. \nFormat your response as: \nMATCH: [Genre Name] \nCONFIDENCE: [X%] \nWHY: [Reasoning based on the genre description I gave you]"
                        }
                    ],
                    "temperature": 0.2
                }
                
                response = requests.post(API_URL, headers=headers, json=data)
                
                if response.status_code == 200:
                    st.info(response.json()['choices'][0]['message']['content'])
                else:
                    st.error("AI connection failed. Check your Groq key.")
    else:
        st.error("ISBN not found.")
