import pandas as pd
import os
from dotenv import load_dotenv
import spotify_helpers as spot

def load_env_variables():
    load_dotenv()
    env_dict = {
        "client_id" : os.getenv("CLIENT_ID"),
        "client_secret" : os.getenv("CLIENT_SECRET"),
        "user_code" : os.getenv("USER_CODE"),
        "user_token":os.getenv("USER_TOKEN"),
        "refresh_token" : os.getenv("REFRESH_TOKEN"),
        "redirect_uri" : "http://127.0.0.1:5500"
    }
    return env_dict
    
def read_csv_names():
    holder = 0
    for files in os.listdir("./data/"):
        if files.endswith(".csv"):
            currentRound = int(files.split("_")[0])
            if currentRound > holder:
                holder = currentRound
    return holder
    
def get_user_input(topseed, bottomseed):
    max_len = 5+max(
        topseed.Track.astype(str).str.len().max() + topseed.Artist.astype(str).str.len().max() + 2,
        bottomseed.Track.astype(str).str.len().max() + bottomseed.Artist.astype(str).str.len().max() + 2 
    )
    print(f'\n{"-"*max_len}')
    print(f"1 {topseed.Track.to_string(index=False)} by: {topseed.Artist.to_string(index=False)}")
    print(f"2 {bottomseed.Track.to_string(index=False)} by: {bottomseed.Artist.to_string(index=False)}")
    userInput = input("Select a song >>>: ")
    print(f'{"-"*max_len}')
    return userInput

def queue_matchup(topseed, bottomseed, env_dict):
    spot.queue_song(topseed.id.to_string(index=False), client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"])
    spot.queue_song(bottomseed.id.to_string(index=False), client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"])
    
def select_matchup(currentRound, env_dict, likedSongs):
    topseed = likedSongs.iloc[0:1]
    bottomseed = likedSongs.iloc[1:2]
        
    queue_matchup(topseed=topseed, bottomseed=bottomseed, env_dict=env_dict)
    
    return topseed, bottomseed

def prev_power_of_two(value):
    return 2**(value.bit_length()-1)