import streamlit as st
import pandas as pd
import requests
import random

TMDB_API_KEY = "8b4a9f9a5f94db0f10d911379650cc6f"

def fetch_tmdb_info(title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    details_url = "https://api.themoviedb.org/3/movie/{}"
    image_base_url = "https://image.tmdb.org/t/p/w500"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }

    search_resp = requests.get(search_url, params=params).json()
    results = search_resp.get("results")
    if not results:
        return {"poster_url": "", "overview": "No description available."}

    movie_id = results[0]["id"]
    details_resp = requests.get(details_url.format(movie_id), params={"api_key": TMDB_API_KEY}).json()

    poster_path = details_resp.get("poster_path", "")
    overview = details_resp.get("overview", "No description available.")
    full_poster_url = f"{image_base_url}{poster_path}" if poster_path else ""

    return {"poster_url": full_poster_url, "overview": overview}

# Load data
df = pd.read_csv("80s_movies.csv")

st.set_page_config(page_title="80s Movie Picker")
st.title("🎬 80s Movie Night Picker")

# Genre Filter
all_genres = sorted(set(
    genre.strip()
    for sublist in df["Genres"].dropna().str.split(";")
    for genre in sublist
))
selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

# Filtered DataFrame
if selected_genre:
    filtered_df = df[df["Genres"].str.contains(selected_genre, na=False)]
else:
    filtered_df = df[df["Viewed"].str.lower() != "yes"]

# Pick a movie
if st.button("🎲 Pick a Random Movie"):
    if not filtered_df.empty:
        movie = filtered_df.sample(1).iloc[0]
        st.session_state["picked_movie"] = movie.to_dict()
    else:
        st.warning("No movies available with that filter.")

# Show the movie
if "picked_movie" in st.session_state:
    movie = st.session_state["picked_movie"]
    st.markdown(f"### 🎥 {movie['Title']}")
    st.markdown(f"**Genre:** {movie['Genres']}")

    tmdb_info = fetch_tmdb_info(movie["Title"])
    if tmdb_info["poster_url"]:
        st.image(tmdb_info["poster_url"], use_container_width=True)
    st.markdown(tmdb_info["overview"])

    if st.button("✅ Mark as Viewed"):
        df.loc[df["Title"] == movie["Title"], "Viewed"] = "Yes"
        df.to_csv("80s_movies.csv", index=False)
        del st.session_state["picked_movie"]
        st.success("Marked as viewed!")