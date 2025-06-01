import streamlit as st
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup

@st.cache_data
def load_data():
    return pd.read_csv("80s_movies.csv")

def fetch_movie_image(title):
    query = f"{title} movie poster"
    url = f"https://www.google.com/search?tbm=isch&q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src")
            if src and "http" in src:
                return src
    except Exception:
        pass
    return None

st.title("🎬 80s Movie Night App")

df = load_data()

page = st.radio("Choose a page:", ["🎲 Pick a Movie", "📤 Upload Movie List"])

if page == "📤 Upload Movie List":
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state["uploaded_df"] = df
else:
    if "uploaded_df" in st.session_state:
        df = st.session_state["uploaded_df"]

    all_genres = sorted(set(
        genre.strip()
        for sublist in df["Genre"].dropna().str.split(";")
        for genre in sublist
    ))
    selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

    if selected_genre:
        filtered_df = df[
            (df["Viewed"].str.lower() != "yes") &
            (df["Genre"].str.contains(selected_genre, case=False, na=False))
        ]
    else:
        filtered_df = df[df["Viewed"].str.lower() != "yes"]

    if st.button("🎲 Pick a Random Movie"):
        if not filtered_df.empty:
            movie = filtered_df.sample(1).iloc[0]
            st.session_state["picked_movie"] = movie.to_dict()

    if "picked_movie" in st.session_state:
        movie = st.session_state["picked_movie"]
        st.markdown(f"### 🎥 {movie['Title']}")
        st.markdown(f"**Genre:** {movie['Genre']}")

        image_url = fetch_movie_image(movie["Title"])
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.info("No image found.")

        if st.button("✅ Mark as Viewed"):
            df.loc[df["Title"] == movie["Title"], "Viewed"] = "Yes"
            st.session_state["uploaded_df"] = df
            df.to_csv("80s_movies.csv", index=False)
            del st.session_state["picked_movie"]
            st.success("Movie marked as viewed!")