import streamlit as st
import pandas as pd
import requests
import os

# Load movie data from CSV in repo
@st.cache_data
def load_movies():
    return pd.read_csv("80s_movies.csv")

# TMDb API key (replace with your actual key or set as environment variable)
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
# Fetch movie poster and overview from TMDb
def fetch_movie_info(title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false"
    }
    response = requests.get(search_url, params=params)
    data = response.json()

    if data.get("results"):
        result = data["results"][0]
        poster_path = result.get("poster_path")
        overview = result.get("overview", "No description available.")
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        return {"image_url": image_url, "overview": overview}

    return {"image_url": None, "overview": "No information found."}

# Main app
st.set_page_config(page_title="🎬 80s Movie Night", layout="centered")
st.title("🎬 80s Movie Night Picker")

df = load_movies()

page = st.radio("Choose a page:", ["🎲 Pick a Movie", "📤 Upload Movie List"])

if page == "📤 Upload Movie List":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully!")

elif page == "🎲 Pick a Movie":
    all_genres = sorted(set(
        genre.strip()
        for sublist in df["Genre"].dropna().str.split(";")
        for genre in sublist
    ))
    selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

    filtered_df = df[df["Viewed"].str.lower() != "yes"]
    if selected_genre:
        filtered_df = filtered_df[filtered_df["Genre"].str.contains(selected_genre, case=False, na=False)]

    if st.button("🎲 Pick a Random Movie"):
        if not filtered_df.empty:
            movie = filtered_df.sample(1).iloc[0]
            st.session_state["picked_movie"] = movie.to_dict()
        else:
            st.warning("No movies match the selected filters.")

    if "picked_movie" in st.session_state:
        movie = st.session_state["picked_movie"]
        st.markdown(f"### 🎥 {movie['Title']}")
        st.markdown(f"**Genre:** {movie['Genre']}")

        tmdb_info = fetch_movie_info(movie["Title"])
        if tmdb_info["image_url"]:
            st.image(tmdb_info["image_url"], use_container_width=True)
        else:
            st.info("No image found.")

        st.markdown(tmdb_info["overview"])

        if st.button("✅ Mark as Viewed"):
            df.loc[df["Title"] == movie["Title"], "Viewed"] = "Yes"
            df.to_csv("80s_movies.csv", index=False)
            st.success(f"Marked '{movie['Title']}' as viewed.")
            del st.session_state["picked_movie"]