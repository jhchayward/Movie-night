import streamlit as st
import pandas as pd
import random

CSV_FILE = "80s_movies.csv"

# Load the movie list from CSV in the repo
@st.cache_data
def load_data():
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

df = load_data()

st.title("🎬 80s Movie Night App")

# Page layout: just one main function now
all_genres = sorted(set(
    genre.strip()
    for sublist in df["Genre"].dropna().str.split(";")
    for genre in sublist
))
selected_genre = st.selectbox("Choose a genre (optional):", [""] + all_genres)

# Filter by genre and unwatched
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

# Display result
if "picked_movie" in st.session_state:
    movie = st.session_state["picked_movie"]
    st.markdown(f"### 🎥 {movie['Title']}")
    st.markdown(f"**Genre:** {movie['Genre']}")
    
    if st.button("✅ Mark as Viewed"):
        idx = df[df["Title"] == movie["Title"]].index
        if not df.loc[idx, "Viewed"].eq("Yes").all():
            df.loc[idx, "Viewed"] = "Yes"
            save_data(df)
            st.success(f"Marked **{movie['Title']}** as viewed.")
            del st.session_state["picked_movie"]