# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from itertools import groupby
from collections import Counter
import dash
import dash_bootstrap_components as dbc
import os
from dotenv import load_dotenv


external_stylesheets = [dbc.themes.LUX]

app = Dash(__name__, external_stylesheets=external_stylesheets)

#HTML head
app.title = 'Spotilyse'
app._favicon = 'favicon.ico'

# Load env
load_dotenv()

#Spotify API Credentials
cid = os.getenv('cid')
secret = os.getenv('secret')

client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

#App Layout
app.layout = html.Div([
    # Navbar
    dbc.Navbar(
        dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="assets/apple-touch-icon.png", height="30px")),
                        dbc.Col(dbc.NavbarBrand("Spotilyse", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]),
        color="black",
        dark=True
    ),

    #Form
    dbc.Container([
        html.H1("Analyse Your Playlist"),
        dbc.Row([
            dbc.Col(
                dbc.FormFloating([
                    dbc.Input(id='playlist_url', type='text', placeholder='Paste Your Spotify Playlist URL Here'),
                    dbc.Label("Paste Your Spotify Playlist URL Here")
                ])
            ),
            dbc.Col(
                dbc.Button(id='submit-button-state', n_clicks=0, children='Analyse'), width="auto"
            )
        ]),

        html.P(id='warning-message', style={'color': 'red'}),
        html.Hr()
    ], className="mt-3",),

    # Playlist Details
    dbc.Container([
        dbc.Row([
            dbc.Col(id='playlist-image'),
            dbc.Col([
                html.H2(id='playlist-name'),
                html.P(id='playlist-owner-name'),
                html.P(id='playlist-description', style={"fontStyle": 'italic'}),
                html.Br(),
                html.P(id='top-genre'),
                html.P(id='top-artist'),
                html.P(id='playlist-followers')
            ]) 
        ])
        
    ])
])

# NavBar
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Get playlist details
@app.callback(Output('playlist-name', 'children'), 
              Output('playlist-description', 'children'),
              Output('playlist-followers', 'children'),
              Output('playlist-owner-name', 'children'),
              Output('playlist-image', 'children'),
              Output('top-genre', 'children'),
              Output('top-artist', 'children'),
              Output('warning-message', 'children'),
              Input('submit-button-state', 'n_clicks'),
              State('playlist_url', 'value'), 
              prevent_initial_call=True)

def get_playlist_details(n_clicks, playlist_url):

    # If nothing is added to the text input but the submit button is clicked, do not update anything
    if playlist_url is None:
        # PreventUpdate prevents ALL outputs updating
        raise dash.exceptions.PreventUpdate

    # Try function 
    try:
    # Function returns a dictionary with playlist details
        fields = "name, description, followers, images, owner"
        fetched_playlist_details = sp.playlist(playlist_url, fields=fields)

        playlist_details = {}
        
        playlist_details["name"] = fetched_playlist_details["name"]
        playlist_details["description"] = fetched_playlist_details["description"]
        playlist_details["followers"] = fetched_playlist_details["followers"]['total']
        playlist_details["image"] = fetched_playlist_details['images'][0]['url']
        playlist_details["owner_url"]= fetched_playlist_details["owner"]['external_urls']['spotify']
        playlist_details["owner_name"] = fetched_playlist_details['owner']['display_name']

        playlist_image = html.Img(src=playlist_details['image'], style={"object-fit":"cover", "width":"450px", "height":"450px","display": "block", "margin": "auto"})
        playlist_owner_name = dcc.Link(f'by {playlist_details["owner_name"]}',href=playlist_details["owner_url"], target="_blank")
        playlist_followers = f'Likes: {playlist_details["followers"]}'
        playlist_description = playlist_details["description"]
        warning_message = ""

        # Tracks_info

        offset = 0
        limit = 100
        results = []

        # Each call only max retrieves 100 tracks, while loop to retrieve all tracks if playlist > 100 tracks
        while True:
            response = sp.playlist_tracks(playlist_url, offset=offset, limit=limit)
            results += response['items']
            if len(response['items']) < limit:
                break
            offset += limit

        track_info = []

        for track in results:
            try:
                #URI
                track_uri = track["track"]["uri"]
            

                #Track name
                track_name = track["track"]["name"]
                
                #Main Artist
                artist_uri = track["track"]["artists"][0]["uri"]
                artist_info = sp.artist(artist_uri)
                
                #Name, popularity, genre
                artist_name = track["track"]["artists"][0]["name"]
                artist_pop = artist_info["popularity"]
                artist_genres = artist_info["genres"]
                
                #Album
                album = track["track"]["album"]["name"]
                
                #Popularity of the track
                track_pop = track["track"]["popularity"]

                row = {
                        "track_uri": track_uri,
                        "track_name": track_name,
                        "artist_uri": artist_uri,
                        "artist_info": artist_info,
                        "artist_name": artist_name,
                        "artist_pop": artist_pop,
                        "artist_genres": artist_genres,
                        "album": album,
                        "track_pop": track_pop
                    }

                track_info.append(row)

            except TypeError:
                pass
            
        track_info_df = pd.DataFrame(track_info)
        

        # Top Genre
        genres_list = []
        for i in range(0,len(track_info_df)):
            genres_list.extend(track_info_df['artist_genres'][i])

        # sort the list (groupby requires sorted input)
        genres_list.sort()

        # group the items by value
        grouped_items = groupby(genres_list)

        # count the frequency of each group
        group_counts = [(key, len(list(group))) for key, group in grouped_items]

        # print the group counts
        #for key, count in group_counts:
            #print(key, count)

        genre_df= pd.DataFrame(group_counts, columns= ['genre', 'count'])

        top_genres = genre_df.nlargest(5,'count').reset_index(drop=True)

        top_genre = f"Top Genre: {top_genres['genre'][0].upper()}"

        # Top Artist

        artists_list = []
        for i in range(0,len(track_info_df)):
            artists_list.append(track_info_df['artist_name'][i])

        # sort the list (groupby requires sorted input)
        artists_list.sort()

        # group the items by value
        grouped_items = groupby(artists_list)

        # count the frequency of each group
        group_counts = [(key, len(list(group))) for key, group in grouped_items]

        # print the group counts
        #for key, count in group_counts:
            #print(key, count)

        artists_df= pd.DataFrame(group_counts, columns= ['artist', 'count'])

        top_artists= artists_df.nlargest(5,'count').reset_index(drop=True)
    
        top_artist = f"Top Artist: {top_artists['artist'][0].upper()}"

        
    # If there are any errors from the code above, return playlist does not exist and dont update the rest of the components
    except Exception:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,'Playlist does not exist!'

    return playlist_details['name'], playlist_description, playlist_followers, playlist_owner_name, playlist_image, top_genre, top_artist, warning_message

if __name__ == '__main__':
    app.run_server(debug=True)

#app.run_server(dev_tools_hot_reload=False)

