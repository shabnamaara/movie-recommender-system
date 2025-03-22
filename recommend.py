import streamlit as st
import pandas as pd
import requests
import pickle
import time

# TMDb API Key
API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

# Function to fetch movie details
def fetch_movie_details(movie_id, retries=3, delay=5):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "overview": data.get("overview", "No description available."),
                "poster_url": f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}" if data.get("poster_path") else None,
                "genres": ", ".join([genre["name"] for genre in data.get("genres", [])]),
                "popularity": data.get("popularity", "N/A"),
                "vote_average": data.get("vote_average", "N/A"),
                "vote_count": data.get("vote_count", "N/A"),
                "release_date": data.get("release_date", "N/A"),
            }
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)

    print("❌ Could not fetch movie details after multiple attempts.")
    return None

# Load movie dataset
def load_movie_data():
    try:
        movies_dict = pickle.load(open("movie.dict.pkl", "rb"))
        similarity = pickle.load(open("similarity.pkl", "rb"))
        return pd.DataFrame(movies_dict), similarity
    except FileNotFoundError:
        st.error("Error: Ensure 'movie.dict.pkl' and 'similarity.pkl' are present.")
        st.stop()

# Recommendation function
def recommend(movie, movies, similarity):
    try:
        index = movies[movies["title"] == movie].index[0]
        distances = sorted(enumerate(similarity[index]), reverse=True, key=lambda x: x[1])
        recommended_movies = []
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].movie_id
            name = movies.iloc[i[0]].title
            details = fetch_movie_details(movie_id)
            recommended_movies.append({
                "title": name,
                "poster": details["poster_url"] if details else None,
                "overview": details["overview"] if details else "No description available."
            })
        return recommended_movies
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []

# Streamlit UI
st.set_page_config(page_title="🎬 Movie Recommender System", layout="wide")

# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ✅ Top Navigation Bar (Session-Based)
st.markdown("""
    <style>
        .topnav {
            background-color: #333;
            overflow: hidden;
            display: flex;
            justify-content: center;
            padding: 10px 0;
        }
        .topnav button {
            background-color: transparent;
            border: none;
            color: white;
            font-size: 18px;
            padding: 14px 20px;
            cursor: pointer;
            font-weight: bold;
        }
        .topnav button:hover {
            background-color: #ddd;
            color: black;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Home"):
        st.session_state.page = "Home"
with col2:
    if st.button("🎥 Recommend Movies"):
        st.session_state.page = "Recommend"
with col3:
    if st.button("📄 Movie Details"):
        st.session_state.page = "Details"
with col4:
    if st.button("📋 All Movies"):
        st.session_state.page = "All"

# Load movie data
movies, similarity = load_movie_data()
movie_list = movies["title"].values

# ✅ Home Page
if st.session_state.page == "Home":
    col1, col2 = st.columns([1.5, 2])
    with col1:
        st.markdown("<h1 style='color: white; font-size: 60px;'>🎬 Movie Recommender System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 24px;'>Get the best movie recommendations instantly. Discover your next favorite film now!</p>", unsafe_allow_html=True)
    with col2:
        st.image("background1.jpg", use_container_width=True)

# ✅ Recommend Movies Page
elif st.session_state.page == "Recommend":
    st.markdown("<h2 style='text-align: center;'>🎥 Movie Recommendations</h2>", unsafe_allow_html=True)
    selected_movie = st.selectbox("Select a Movie...", movie_list, index=0)

    if st.button("Recommend"):
        recommended_movies = recommend(selected_movie, movies, similarity)
        if recommended_movies:
            st.subheader("Recommended Movies:")
            cols = st.columns(5)
            for i, movie in enumerate(recommended_movies):
                with cols[i]:
                    st.text(movie["title"])
                    if movie["poster"]:
                        st.image(movie["poster"], use_container_width=True)
                    else:
                        st.text("🚫 Poster Not Available")

# ✅ Movie Details Page
elif st.session_state.page == "Details":
    st.markdown("<h2 style='text-align: center;'>📄 Movie Details</h2>", unsafe_allow_html=True)
    selected_movie = st.selectbox("Select a Movie...", movie_list, index=0)

    if st.button("Show Details"):
        movie_id = movies[movies["title"] == selected_movie].iloc[0].movie_id
        details = fetch_movie_details(movie_id)
        if details:
            col1, col2 = st.columns([1, 2])
            with col1:
                if details["poster_url"]:
                    st.image(details["poster_url"], caption=selected_movie, use_container_width=True)
                else:
                    st.write("🚫 No poster available")
            with col2:
                st.subheader(f"{selected_movie}")
                st.write(f"*Overview:* {details['overview']}")
                st.write(f"*Genres:* {details['genres']}")
                st.write(f"*Popularity:* {details['popularity']}")
                st.write(f"*Vote Average:* {details['vote_average']} ⭐")
                st.write(f"*Vote Count:* {details['vote_count']}")
                st.write(f"*Release Date:* {details['release_date']}")
        else:
            st.error("❌ Movie details could not be fetched. Try another movie.")

# ✅ All Movies Page
elif st.session_state.page == "All":
    st.markdown("<h2 style='text-align: center;'>📋 All Available Movies</h2>", unsafe_allow_html=True)

    all_movie_names = movies['title'][:100]
    all_movie_ids = movies['movie_id'][:100]
    cols = st.columns(5)
    for i in range(len(all_movie_names)):
        name = all_movie_names[i]
        movie_id = all_movie_ids[i]
        details = fetch_movie_details(movie_id)
        with cols[i % 5]:
            st.text(name)
            if details and details['poster_url']:
                st.image(details['poster_url'], use_container_width=True)
            else:
                st.text("🚫 Poster Not Available")
