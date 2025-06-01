import streamlit as st
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup

CSV_FILE = "80s_movies.csv"

# Load or create movie list
@st.cache_data
def load_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Title", "Genre", "Viewed"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def fetch_imdb_data(title):
    try:
        search_url = f"https://www.imdb.com/find?q={requests.utils.quote(title)}&s=tt&ttype=ft&ref_=fn_ft"
        search_res = requests.get(search_url, headers={"Accept-Language": "en-US,en;q=0.5"})
        search_soup = BeautifulSoup(search_res.content, "html.parser")

        first_result = search_soup.select_one(".findList .findResult a")
        if not first_result or not first_result['href']:
            return {"cover_url": None, "plot": "No IMDb match found."}

        movie_url = "https://www.imdb.com" + first_result["href"]
        movie_res = requests.get(movie_url, headers={"Accept-Language": "en-US,en;q=0.5"})
        movie_soup = BeautifulSoup(movie_res.content, "html.parser")

        image_tag = movie_soup.find("img", {"class": "ipc-image"})
        image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else None

        plot_tag = movie_soup.find("span", {"data-testid": "plot-xl"})
        plot = plot_tag.text.strip() if plot_tag else "No plot summary available."

        return {"cover_url": image_url, "plot": plot}

    except Exception as e:
        return {"cover_url": None, "plot": f"Error fetching data: {e}"}

df = load_data()

st.title("🎬 80s Movie Night App")

page = st.radio("Choose a page:", ["🎲 Pick a Movie", "📤 Upload Movie List"])

# --------- Page 1: Pick a Movie ---------
if page == "🎲 Pick a Movie":
    all_genres = sorted(set(genre.strip() for sublist in df["Genre"].dropna().str.split(";") for genre in sublist))
    selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

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

    if "picked_movie" in st.session_state:
        movie = st.session_state["picked_movie"]
        st.markdown(f"### 🎥 {movie['Title']}")
        st.markdown(f"**Genre:** {movie['Genre']}")

        imdb_info = fetch_imdb_data(movie["Title"])
        if imdb_info["cover_url"]:
            st.image(imdb_info["cover_url"], use_container_width=True)
        st.markdown(imdb_info["plot"])

        if st.button("✅ Mark as Viewed"):
            idx = df[df["Title"] == movie["Title"]].index
            if not df.loc[idx, "Viewed"].eq("Yes").all():
                df.loc[idx, "Viewed"] = "Yes"
                save_data(df)
                st.success(f"Marked **{movie['Title']}** as viewed.")
                del st.session_state["picked_movie"]

# --------- Page 2: Upload CSV ---------
elif page == "📤 Upload Movie List":
    st.markdown("Upload a CSV with columns: Title, Genre, Viewed")
    uploaded = st.file_uploader("Choose CSV file", type="csv")
    if uploaded:
        new_df = pd.read_csv(uploaded)
        if set(["Title", "Genre", "Viewed"]).issubset(new_df.columns):
            new_df.to_csv(CSV_FILE, index=False)
            st.success("Uploaded new movie list! Refresh the page to load it.")
        else:
            st.error("CSV must contain columns: Title, Genre, Viewed")