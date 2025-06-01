import streamlit as st
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup

CSV_FILE = "80s_movies.csv"

# Load the CSV from repo
@st.cache_data
def load_data():
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# IMDb scraping via DuckDuckGo
def fetch_imdb_data(title):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://duckduckgo.com/html/?q=site:imdb.com+{title.replace(' ', '+')}"
    res = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    links = soup.find_all("a", href=True)
    imdb_link = next((link['href'] for link in links if "imdb.com/title/" in link['href']), None)

    if imdb_link:
        imdb_res = requests.get(imdb_link, headers=headers)
        imdb_soup = BeautifulSoup(imdb_res.text, "html.parser")

        poster = imdb_soup.find("meta", property="og:image")
        image_url = poster["content"] if poster else ""

        description = imdb_soup.find("meta", property="og:description")
        plot = description["content"] if description else "No description found."

        return {
            "title": title,
            "plot": plot,
            "cover_url": image_url
        }
    return {"title": title, "plot": "No IMDb page found.", "cover_url": ""}

# Load data
df = load_data()

# UI setup
st.title("🎬 80s Movie Night")

page = st.radio("Choose a page:", ["🎲 Pick a Movie", "📤 Upload Movie List"])

# ----------- PAGE 1: PICK A MOVIE -----------
if page == "🎲 Pick a Movie":
    # Genre filter
    all_genres = sorted(set(g.strip() for sub in df["Genre"].dropna().str.split(";") for g in sub))
    selected_genre = st.selectbox("Filter by genre (optional):", [""] + all_genres)

    if selected_genre:
        filtered_df = df[(df["Viewed"] != "Yes") & (df["Genre"].str.contains(selected_genre, case=False, na=False))]
    else:
        filtered_df = df[df["Viewed"] != "Yes"]

    if st.button("🎲 Pick a Random Movie"):
        if not filtered_df.empty:
            movie = filtered_df.sample(1).iloc[0]
            st.session_state["picked_movie"] = movie.to_dict()
        else:
            st.warning("No unwatched movies match that genre.")

    # Display picked movie
    if "picked_movie" in st.session_state:
        movie = st.session_state["picked_movie"]
        st.markdown(f"### 🎥 {movie['Title']}")
        st.markdown(f"**Genre:** {movie['Genre']}")

        imdb_info = fetch_imdb_data(movie["Title"])
        st.image(imdb_info["cover_url"], use_column_width=True)
        st.markdown(imdb_info["plot"])

        if st.button("✅ Mark as Viewed"):
            idx = df[df["Title"] == movie["Title"]].index
            if not df.loc[idx, "Viewed"].eq("Yes").all():
                df.loc[idx, "Viewed"] = "Yes"
                save_data(df)
                st.success(f"Marked **{movie['Title']}** as viewed.")
                del st.session_state["picked_movie"]

# ----------- PAGE 2: UPLOAD MOVIE LIST -----------
elif page == "📤 Upload Movie List":
    st.markdown("Upload a CSV with columns: Title, Genre, Viewed")
    uploaded = st.file_uploader("Choose a file", type="csv")
    if uploaded:
        new_df = pd.read_csv(uploaded)
        if set(["Title", "Genre", "Viewed"]).issubset(new_df.columns):
            new_df.to_csv(CSV_FILE, index=False)
            st.success("Uploaded! Refresh to load new list.")
        else:
            st.error("CSV must include: Title, Genre, Viewed")
