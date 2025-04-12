# requirements.txt
# spotipy==2.22.1
# pandas==1.5.3
# streamlit==1.18.1

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import streamlit as st

# Spotify API credentials
CLIENT_ID = "8885c24930044341946150b850ff2579"
CLIENT_SECRET = "adec735b262b4d02b6e2858cfc321f21"

# Authenticate Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def get_playlist_data(playlist_link):
    """Extract data from a Spotify playlist."""
    playlist_uri = playlist_link.split("/")[-1].split("?")[0]
    tracks = sp.playlist_tracks(playlist_uri)["items"]

    data = []
    for track in tracks:
        track_info = track["track"]
        artist_info = sp.artist(track_info["artists"][0]["id"])
        
        data.append({
            "Track Name": track_info["name"],
            "Artist": track_info["artists"][0]["name"],
            "Genre": ", ".join(artist_info.get("genres", [])),
            "Album": track_info["album"]["name"],
            "Popularity": track_info["popularity"],
            "Duration (ms)": track_info["duration_ms"],
            "Country": artist_info.get("country", "Unknown"),
        })
    return pd.DataFrame(data)

def visualize_data(df):
    """Create a dashboard to visualize playlist data."""
    st.title("Spotify Playlist Dashboard")
    
    # Display raw data
    st.subheader("Playlist Data")
    st.dataframe(df)
    
    # Plot song popularity
    st.subheader("Song Popularity")
    st.bar_chart(df[["Track Name", "Popularity"]].set_index("Track Name"))
    
    # Plot song duration
    st.subheader("Song Duration")
    st.bar_chart(df[["Track Name", "Duration (ms)"]].set_index("Track Name"))

def main():
    """Main function to run the app."""
    st.sidebar.title("Spotify Playlist Analyzer")
    playlist_link = st.sidebar.text_input("Enter Spotify Playlist Link:", "")
    
    if playlist_link:
        df = get_playlist_data(playlist_link)
        visualize_data(df)

if __name__ == "__main__":
    main()
