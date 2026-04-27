import streamlit as st
import requests

# --- CONFIGURATION ---
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# --- APP SESSION STATE (Memory for Custom Genres) ---
if "custom_categories" not in st.session_state:
    # Starter examples based on your previous list
    st.session_state.custom_categories = [
        {"name": "Missing Folk", "desc": "Stories involving disappearances and the search for people."},
        {"name": "Messed Up Families", "desc": "Focuses on complex, toxic, or dramatic family secrets and relationships."}
    ]

# --- SIDEBAR: GENRE MANAGER ---
with st.sidebar:
    st.header("🛠️ Bespoke Genre Builder")
    st.write("Define your custom categories:")
    
    with st.form("new_genre_form", clear_on_submit=True):
        new_name = st.text_input("Genre Name")
        new_desc = st.text_area("Description")
        add_btn = st.form_submit_button("Add to List")
        
        if add_btn and new_name and new_desc:
            st.session_state.custom_categories.append({"name": new_name, "desc": new_desc})
            st.rerun()

    if st.button("🗑️ Clear All & Reset"):
        st.session_state.custom_categories = []
        st.rerun()

    st.write("---")
    st.write("**Current Custom Genres:**")
    for cat in st.session_state.custom_categories:
        st.caption(f"• **{cat['name']}**")

# --- MAIN APP UI ---
st.set_page_config(page_title="Genre Detective", page_icon="🕵️‍♀️")
st.title("🕵️‍♀️ Bespoke Genre Detective")

# --- STEP 1: ISBN INPUT ---
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
        
        # Safe subject extraction
        raw_subjects = book_data.get('subjects', [])
        subject_names = [s.get('name') if isinstance(s, dict) else str(s) for s in raw_subjects]
        clean_subjects = ", ".join(subject_names[:10])
        
        st.success(f"📖 Found: **{title}**")
        if 'cover' in book_data:
            st.image(book_data['cover'].get('medium', ''), width=150)

        # --- STEP 2: PARSED AI CLASSIFICATION ---
        st.markdown("---")
        if not st.session_state.custom_categories:
            st.warning("Please add custom genres in the sidebar to begin analysis.")
        else:
            with st.spinner("🧠 Categorizing against your bespoke rules..."):
                genre_guide = "\n".join([f"- {c['name']}: {c['desc']}" for c in st.session_state.custom_categories])
                
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                
                data = {
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a book expert. Use ONLY these custom genres: \n{genre_guide}"
                        },
                        {
                            "role": "user", 
                            "content": f"Book: {title}. Themes: {clean_subjects}. \n\nIMPORTANT: Respond ONLY in this exact format: \nPRIMARY: [Genre Name] \nSECONDARY: [Genre Name] \nWHY: [Detailed reasoning based on the bespoke descriptions provided]"
                        }
                    ],
                    "temperature": 0.1
                }
                
                response = requests.post(API_URL, headers=headers, json=data)
                
                if response.status_code == 200:
                    output = response.json()['choices'][0]['message']['content']
                    
                    # Split the output into lines and display them formatted
                    lines = output.strip().split("\n")
                    for line in lines:
                        if ":" in line:
                            label, content = line.split(":", 1)
                            st.subheader(label.strip())
                            st.write(content.strip())
                else:
                    st.error(f"AI Error ({response.status_code}). Please check your Groq API Key.")
    else:
        st.error(f"ISBN {isbn} not found in Open Library.")

st.markdown("---")
st.caption("Custom Classifier Stable | April 2026")
