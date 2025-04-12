import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import streamlit as st
import os
import time
from dotenv import load_dotenv
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt

load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not CLIENT_ID:
    st.error("SPOTIPY_CLIENT_ID is not set in the environment variables.")
    st.stop()

# Authenticate Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def get_all_tracks(playlist_uri):
    """Fetch all tracks from a playlist using pagination."""
    results = []
    offset = 0
    while True:
        try:
            response = sp.playlist_tracks(playlist_uri, offset=offset)
            if not response or 'items' not in response:
                break
            results.extend(response['items'])
            time.sleep(0.1)  # Add delay to prevent rate limiting
            if len(response['items']) < 100:
                break
            offset += 100
        except Exception as e:
            print(f"Error fetching tracks: {e}")
            break
    return results

def get_playlist_data(playlist_link):
    """Extract metadata and track details from a Spotify playlist."""
    try:
        playlist_uri = playlist_link.split("/")[-1].split("?")[0]
    except Exception as e:
        st.error(f"Error processing playlist link: {e}")
        return None, None
    
    try:
        playlist_info = sp.playlist(playlist_uri)
    except Exception as e:
        st.error(f"Could not retrieve playlist info: {e}")
        return None, None
    
    # Playlist metadata
    metadata = {
        "Name": playlist_info["name"],
        "Description": playlist_info.get("description", "No description available"),
        "Thumbnail": playlist_info["images"][0]["url"] if playlist_info.get("images") else None,
        "Likes": playlist_info.get("followers", {}).get("total", 0),
        "Total Tracks": playlist_info["tracks"]["total"]
    }
    
    # Fetch all tracks using pagination
    tracks_data = get_all_tracks(playlist_uri)
    if not tracks_data:
        st.error("Could not retrieve tracks for this playlist.")
        return metadata, pd.DataFrame()
    
    # Track details
    tracks = []
    for item in tracks_data:
        track = item["track"]
        if not track:
            continue
        
        try:
            artist_info = sp.artist(track["artists"][0]["id"])
            #audio_features = sp.audio_features(track["id"])[0] if track["id"] else {}
            audio_features = {}
        except Exception as e:
            print(f"Error fetching artist info: {e}")
            audio_features = {}
        
         # Extract release year
        release_date = track["album"]["release_date"]
        try:
            release_year = int(release_date[:4])
        except:
            release_year = None

        # Confirm track name and popularity are available
        track_name = track.get("name", "Unknown Track")
        track_popularity = track.get("popularity", 0)

        track_data = {
            "Track Name": track_name,
            "Track ID": track.get("id", "No ID"),
            "Artist": track["artists"][0]["name"] if track["artists"] else "Unknown Artist",
            "Artist ID": track["artists"][0]["id"] if track["artists"] else "Unknown ID",
            "Album": track["album"]["name"] if track["album"] else "Unknown Album",
            "Album Release Date": release_date,
            "Release Year": release_year,
            "External URL": track["external_urls"].get("spotify", None) if track["external_urls"] else "No URL",
            "Popularity": track_popularity,
            "Genres": ", ".join(artist_info.get("genres", [])) if artist_info else "No Genres",
        }
        tracks.append(track_data)

    # Verify DataFrame is not empty and contains data
    if not tracks:
        st.error("No track data available to create DataFrame.")
        return metadata, pd.DataFrame()

    df = pd.DataFrame(tracks)

    # Convert necessary columns to numeric, handling errors by coercing invalid values to NaN
    cols_to_numeric = ['Popularity']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.write("DataFrame Sample:")  # Debug: Display sample DataFrame
    st.dataframe(df.head())

    return metadata, df
    
def visualize_data(metadata, df):
    """Create a Streamlit dashboard to visualize Spotify playlist data."""
    st.title("Spotify Playlist Dashboard")
    
    # Display metadata
    st.subheader("Playlist Metadata")
    st.write(f"**Name:** {metadata['Name']}")
    st.write(f"**Description:** {metadata['Description']}")
    st.write(f"**Likes:** {metadata['Likes']}")
    st.write(f"**Total Tracks:** {metadata['Total Tracks']}")
    if metadata['Thumbnail']:
        st.image(metadata['Thumbnail'], width=300)
    
    # Display raw data
    st.subheader("Track Details")
    st.dataframe(df)
    
    # Release Year Distribution
    if 'Release Year' in df.columns:
        st.subheader("Release Year Distribution")
        release_year_counts = df['Release Year'].dropna().astype(int).value_counts().sort_index()
        st.bar_chart(release_year_counts)
    else:
        st.error("Release Year data is missing.")

    # Popularity Histogram
    if 'Track Name' in df.columns and 'Popularity' in df.columns:
        st.subheader("Popularity Distribution")
        fig, ax = plt.subplots()
        ax.hist(df['Popularity'], bins=20, color = 'skyblue')
        ax.set_xlabel("Popularity")
        ax.set_ylabel("Number of Tracks")
        st.pyplot(fig)
    else:
        st.error("Popularity data is missing.")
    
    # Genre Word Cloud
    if 'Genres' in df.columns:
        st.subheader("Genre Word Cloud")
        genre_text = ' '.join(df['Genres'].dropna())
        if genre_text:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(genre_text)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.write("No genre data available to create word cloud.")
    else:
        st.error("Genres data is missing.")
    
def main():
    """Main function to run the Streamlit app."""
    st.sidebar.title("Spotify Playlist Analyzer")
    playlist_link = st.sidebar.text_input("Enter Spotify Playlist Link:", "")
    
    # More flexible playlist link validation
    if playlist_link and "spotify.com/playlist/" not in playlist_link:
        st.error("Please enter a valid Spotify playlist link.")
        return
    
    if playlist_link:
        try:
            with st.spinner("Fetching playlist data..."):
                metadata, df = get_playlist_data(playlist_link)
            if df is not None and not df.empty:
                visualize_data(metadata, df)
            else:
                st.error("No data to visualize.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
