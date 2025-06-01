from imdb import IMDb

ia = IMDb()

def fetch_imdb_data(title):
    search_results = ia.search_movie(title)
    if search_results:
        movie = ia.get_movie(search_results[0].movieID)
        return {
            "title": movie.get("title"),
            "year": movie.get("year"),
            "plot": movie.get("plot outline", "No description available."),
            "cover_url": movie.get("cover url", "")
        }
    return None

# Inside the picked movie display logic
imdb_data = fetch_imdb_data(movie["Title"])
if imdb_data:
    st.image(imdb_data["cover_url"], width=300)
    st.markdown(f"**IMDb Summary:** {imdb_data['plot']}")