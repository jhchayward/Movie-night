import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# TMDb API
TMDB_API_KEY = st.secrets["tmdb_api_key"]

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], SCOPE)
gc = gspread.authorize(CREDENTIALS)

SHEET_NAME = "80s_movies"
worksheet = gc.open(SHEET_NAME).sheet1

# Load movie data
@st.cache_data(ttl=60)
def load_data():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_data(df):
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

# TMDb movie lookup
def fetch_movie_info(title):
    url = f"https://api.themoviedb.org/3/search/movie?query={title}&api_key={TMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            result = data["results"][0]
            poster_path = result.get("poster_path")
            overview = result.get("overview", "No description available.")
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            return {"image_url": image_url, "overview": overview}
    return {"image_url": None, "overview": "No information found."}

# UI
st.title("🎬 80s Movie Night App")
page = st.radio("Choose a page:", ["🎲 Pick a Movie", "🧪 Test Google Sheet Connection"])

df = load_data()

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

        tmdb_data = fetch_movie_info(movie["Title"])
        if tmdb_data["image_url"]:
            st.image(tmdb_data["image_url"], use_container_width=True)
        st.markdown(tmdb_data["overview"])

        if st.button("✅ Mark as Viewed"):
            idx = df[df["Title"].str.strip().str.lower() == movie["Title"].strip().lower()].index
            if not df.loc[idx, "Viewed"].eq("Yes").all():
                df.loc[idx, "Viewed"] = "Yes"
                save_data(df)
                st.success(f"Marked **{movie['Title']}** as viewed.")
                del st.session_state["picked_movie"]

elif page == "🧪 Test Google Sheet Connection":
    try:
        test_data = worksheet.get_all_records()
        st.success(f"Successfully connected to Google Sheet. {len(test_data)} rows loaded.")
    except Exception as e:
        st.error(f"Error connecting to Google Sheet: {e}")
