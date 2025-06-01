import streamlit as st
import pandas as pd
import requests
import random

CSV_FILE = "80s_movies.csv"
OMDB_API_KEY = "ca8532b8"  # Replace this with your real API key

# Load movie data
@st.cache_data
def load_data():
    return pd.read_csv(CSV_FILE)

df = load_data()

st.title("🎬 80s Movie Night App")

page = st.radio("Choose a page:", ["🎲 Pick a Movie", "📤 Upload Movie List"])

def fetch_movie_info(title):
    params = {
        "t": title,
        "apikey": OMDB_API_KEY
    }
    response = requests.get("http://www.omdbapi.com/", params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return {
                "poster": data.get("Poster"),
                "plot": data.get("Plot")
            }
    return {"poster": None, "plot": "No plot found."}

# --------- Page 1: Pick a Movie ---------
if page == "🎲 Pick a Movie":
    all_genres = sorted(set(
        genre.strip()
        for sublist in df["Genres"].dropna().str.split(";")
        for genre in sublist
    ))
    selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

    if selected_genre:
        filtered_df = df[(df["Viewed"] != "Yes") & (df["Genres"].str.contains(selected_genre, case=False, na=False))]
    else:
        filtered_df = df[df["Viewed"] != "Yes"]

    if st.button("🎲 Pick a Random Movie"):
        if not filtered_df.empty:
            movie = filtered_df.sample(1).iloc[0]
            st.session_state["picked_movie"] = movie.to_dict()
        else:
            st.warning("No unwatched movies match that genre.")

    if "picked_movie" in st.session_state:
        movie = st.session_state["picked_movie"]
        st.markdown(f"### 🎥 {movie['Film Title']}")
        st.markdown(f"**Genre:** {movie['Genres']}")

        imdb_info = fetch_movie_info(movie["Film Title"])
        if imdb_info["poster"]:
            st.image(imdb_info["poster"], use_container_width=True)
        st.markdown(imdb_info["plot"])

        if st.button("✅ Mark as Viewed"):
            idx = df[df["Film Title"] == movie["Film Title"]].index
            if not df.loc[idx, "Viewed"].eq("Yes").all():
                df.loc[idx, "Viewed"] = "Yes"
                df.to_csv(CSV_FILE, index=False)
                st.success(f"Marked **{movie['Film Title']}** as viewed.")
                del st.session_state["picked_movie"]

# --------- Page 2: Upload CSV ---------
elif page == "📤 Upload Movie List":
    st.markdown("Upload a CSV with columns: Film Title, Genres, Viewed")
    uploaded = st.file_uploader("Choose CSV file", type="csv")
    if uploaded:
        new_df = pd.read_csv(uploaded)
        if set(["Film Title", "Genres", "Viewed"]).issubset(new_df.columns):
            new_df.to_csv(CSV_FILE, index=False)
            st.success("Uploaded new movie list! Refresh the page to load it.")
        else:
            st.error("CSV must contain columns: Film Title, Genres, Viewed")