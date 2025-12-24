import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Page Config
st.set_page_config(
    page_title="Cinematch",
    layout="wide",
    page_icon="🎥"
)

# Custom CSS
st.markdown("""
    <style>
    /* --- FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* Global settings */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: #E0E0E0;
    }

    /* Hide Streamlit Top Bar/Header */
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden; height: 0px;}

    /* Main Background */
    .stApp {
        background-color: #121212;
        margin-top: -30px; /* Pull up content since header is gone */
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 1px solid #333;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: transparent;
        border: none;
        color: #fff;
        font-weight: 600;
        font-size: 20px; /* Increased Font Size */
    }
    .stTabs [aria-selected="true"] {
        color: #fff;
        border-bottom: 2px solid #fff;
    }

    /* --- SEARCH BAR --- */
    /* Input Box */
    .stSelectbox > div > div {
        background-color: #1E1E1E !important;
        border: 1px solid #333 !important;
        color: white !important;
        border-radius: 4px !important;
        min-height: 48px !important;
    }
    /* Text inside */
    .stSelectbox div[data-baseweb="select"] > div {
        color: white !important;
        font-size: 16px !important;
    }
    /* SVG Icon */
    .stSelectbox svg {
        fill: #888 !important;
    }
    /* Dropdown Menu */
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
    }
    li[data-baseweb="option"] {
        color: #000000 !important;
    }
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
    }

    /* --- BUTTON --- */
    /* Targeting the button to align effectively */
    .stButton > button {
        background-color: #E0E0E0 !important;
        color: #000000 !important;
        border: none;
        padding: 0px 24px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 4px;
        width: 100%;
        height: 48px; /* Match Input Height */
        line-height: 48px;
        margin-top: 0px; /* Reset margins for alignment */
    }
    /* Ensure text inside is also black */
    .stButton > button p {
        color: #000000 !important;
    }
    .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        box-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    .stButton > button:active {
        background-color: #cccccc !important;
    }

    /* --- MOVIE CARDS --- */
    a { 
        text-decoration: none !important; 
        color: inherit !important;
    }
    
    .movie-card {
        background-color: #1E1E1E;
        border-radius: 8px;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        border: 1px solid #333;
        display: flex;
        flex-direction: column;
    }
    
    .movie-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.5);
        border-color: #555;
        cursor: pointer;
    }

    .movie-poster {
        width: 100%;
        aspect-ratio: 2/3;
        object-fit: cover;
        display: block;
        background-color: #000;
    }

    .movie-title {
        padding: 12px;
        text-align: center;
        font-size: 14px;
        font-weight: 600;
        color: #eee;
        background-color: #1E1E1E;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
    
    /* General Text - Force White for readability */
    p, li, label, .stMarkdown {
        color: #FFFFFF !important;
        line-height: 1.6;
    }
    strong {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    </style>
    """, unsafe_allow_html=True)

# Helper Function to Fetch Poster (Using OMDb API as backup for TMDB)
def fetch_poster(title):
    # OMDb API Key (Free tier, 1000 daily limit)
    # Using a common demo key 'trilogy' which is often available, or you can use your own.
    api_key = "f49e77fe" # Should be a valid key
    url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_url = data.get('Poster')
        
        if poster_url and poster_url != "N/A":
            return poster_url
    except Exception:
        pass
    
    # Fallback: Dark modern placeholder
    return "https://via.placeholder.com/500x750/111111/333333?text=No+Preview"

# Load Data
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movies.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

try:
    movies, similarity = load_data()
except FileNotFoundError:
    st.error("Data files missing.")
    st.stop()

# Recommendation Logic
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        recommended_movies = []
        recommended_posters = []
        
        # We need to fetch posters by TITLE now, not ID
        movie_titles_for_api = []
        
        for i in movies_list:
            title = movies.iloc[i[0]].title
            recommended_movies.append(title)
            movie_titles_for_api.append(title)
            
        with ThreadPoolExecutor() as executor:
            recommended_posters = list(executor.map(fetch_poster, movie_titles_for_api))
            
        return recommended_movies, recommended_posters
    except Exception:
        return [], []

# --- APP LAYOUT ---
st.title("Cinematch")

# Tabs
tab1, tab2 = st.tabs(["Home", "About"])

# TAB 1: HOME
with tab1:
    st.markdown("### Find your next watch")
    st.write("") # Spacer
    
    # Using 'vertical_alignment' to align the button perfectly with the input box
    # If this fails in older Streamlit, it will just ignore the argument or error out. 
    # But this is the cleaner way if version allows. 
    # If not, CSS 'margin-top: 0px' + container alignment helps.
    try:
        col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
    except TypeError:
        # Fallback for older Streamlit versions
        col1, col2 = st.columns([5, 1])

    with col1:
        selected_movie_name = st.selectbox(
            "Search for a movie",
            movies['title'].values,
            index=0,
            label_visibility="visible" # Showing label to ensure alignment space is reserved
        )
    
    with col2:
        # Button text is now "Recommend"
        recommend_clicked = st.button('Recommend')

    if recommend_clicked:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.spinner('Searching...'):
            names, posters = recommend(selected_movie_name)
        
        if names:
            st.markdown(f"Top recommendations for **{selected_movie_name}**:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            cols = st.columns(5)
            for idx, col in enumerate(cols):
                with col:
                    # Google Search URL
                    search_query = urllib.parse.quote(names[idx] + " movie")
                    google_url = f"https://www.google.com/search?q={search_query}"
                    
                    # Added loading="lazy" for optimization
                    st.markdown(f"""
                    <a href="{google_url}" target="_blank">
                        <div class="movie-card">
                            <img src="{posters[idx]}" class="movie-poster" loading="lazy">
                            <div class="movie-title">{names[idx]}</div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No recommendations found.")

# TAB 2: ABOUT
with tab2:
    st.header("About the Project")
    st.markdown("""
    ### 🎬 Cinematch: Intelligent Movie Recommendations
    
    Welcome to **Cinematch**, a premium movie discovery platform designed to solve the "what to watch next" dilemma. This project blends advanced data science with a sleek, user-centric interface.
    
    #### � Project Execution & Methodology
    
    The development of Cinematch followed a rigorous pipeline:
    
    **1. Data Acquisition**
    *   We utilized the **TMDB 5000 Movies Dataset**, a rich repository of film metadata.
    *   Key attributes like *Genres, Keywords, Cast, Crew, and Plot Overviews* were extracted to form the backbone of our recommendation logic.
    
    **2. Data Preprocessing & Cleaning**
    *   Raw data was cleaned to handle missing values and duplicates.
    *   Textual data was processed using **Natural Language Processing (NLP)** techniques, including tokenization and stemming, to standardize the vocabulary.
    
    **3. Feature Engineering (The AI Core)**
    *   We implemented a **Bag-of-Words** model using `CountVectorizer`.
    *   This converted our processed text tags into 5,000 distinct numerical features, creating a mathematical "fingerprint" for every movie.
    
    **4. The Algorithm: Cosine Similarity**
    *   To find matches, we calculated the **Cosine Similarity** between movie vectors.
    *   This measures the angular distance between films in multi-dimensional space, allowing us to recommend movies that are effectively "nearest neighbors" in terms of content and style.
    
    ---
    
    #### 🏆 Credits & Acknowledgments
    
    *   **Lead Developer:**  
        **Vanshish Chaturvedi**  
        *(Concept, Architecture, and Implementation)*
        
    *   **AI Co-Pilot:**  
        Built with the assistance of advanced **AI Coding Agents** for optimization and refinement.
        
    *   **Data Source:**  
        **TMDB (The Movie Database)**
        
    *   **Visual Assets:**  
        Poster art dynamically served via the **OMDb API**.
    
    ---
    *© 2025 Vanshish Chaturvedi. All Rights Reserved.*
    """)

