import pandas as pd
import os
import spotify_helpers as spot
import ranking_helpers as rank_help

def save_choice(topseed, bottomseed, likedSongs, matchups, roundWinners, roundLosers):
        likedSongs.to_csv('./data/'+currentRound+'_starting.csv', index=False)
        roundWinners.to_csv('./data/'+currentRound+'_winners.csv', index=False)
        roundLosers.to_csv('./data/'+currentRound+'_losers.csv', index=False)
        matchups.to_csv('./data/'+currentRound+'_matchups.csv', index=False)
        
def is_integer(input_string):
    try: 
        int(input_string)
        return True
    except ValueError:
        return False

def read_user_input(input, likedSongs, matchups, roundWinners, roundLosers):
    if input == 'stop':
        return 'stop', likedSongs, matchups, roundWinners, roundLosers
    # Check if User requested to Requeue Song
    elif input == "rq":
        rank_help.queue_matchup(topseed=topseed, bottomseed=bottomseed, env_dict=env_dict)
        input = 'restart'
        
    # Check if user input is an integer
    if not is_integer(input):
        input = 0
        
    # User Selected the top seed as the winner #
    if 1 == int(input):
        roundWinners = pd.concat([roundWinners, topseed], ignore_index=True)
        roundLosers = pd.concat([roundLosers, bottomseed], ignore_index=True)
    # User selected the bottom seed as the winner
    elif 2 == int(input):
        roundWinners = pd.concat([roundWinners, bottomseed], ignore_index=True)
        roundLosers = pd.concat([roundLosers, topseed], ignore_index=True)
    else:
        input = 'restart'

    if input != 'restart':
        likedSongs = likedSongs.drop(topseed.index)
        likedSongs = likedSongs.drop(bottomseed.index)
        matchups = pd.concat([matchups, topseed, bottomseed], ignore_index=True)
        save_choice(topseed=topseed, bottomseed=bottomseed, likedSongs=likedSongs, matchups=matchups, roundWinners=roundWinners, roundLosers=roundLosers)
        
    return input, likedSongs, matchups, roundWinners, roundLosers
        
def create_next_round(likedSongs, matchups, roundWinners, currentRound, nextRound, headers):
    if len(likedSongs) == 1:
        roundWinners = pd.concat([roundWinners, likedSongs.sample(n=1)], ignore_index=True)
        matchups = pd.concat([matchups, likedSongs.sample(n=1)], ignore_index=True)
        
    print("\nCreating files for Round "+nextRound)
    roundWinners.to_csv('./data/'+nextRound+'_starting.csv', index=False)
    print(nextRound+'_starting.csv Complete')
    roundWinners.to_csv('./data/backup/'+nextRound+'_startingbackup.csv', index=False)
    print(nextRound+'_startingbackup.csv Complete')
    pd.DataFrame(columns=headers).to_csv('./data/'+nextRound+'_losers.csv', index=False)
    print(nextRound+'_losers.csv Complete')
    pd.DataFrame(columns=headers).to_csv('./data/'+nextRound+'_winners.csv', index=False)
    print(nextRound+'_winners.csv Complete')
    pd.DataFrame(columns=headers).to_csv('./data/'+nextRound+'_matchups.csv', index=False)
    print(nextRound+'_matchups.csv Complete')
    
    currentRound = nextRound
    nextRound = str(int(nextRound)+1)
    print("Welcome to round "+currentRound+"!\n")
    return currentRound, nextRound

def read_current_round(currentRound):
    likedSongs = pd.read_csv('./data/'+currentRound+'_starting.csv', sep=',', header=0)
    roundWinners = pd.read_csv('./data/'+currentRound+'_winners.csv', sep=',', header=0)
    roundLosers = pd.read_csv('./data/'+currentRound+'_losers.csv', sep=',', header=0)
    matchups = pd.read_csv('./data/'+currentRound+'_matchups.csv', sep=',', header=0)
    
    return likedSongs, roundWinners, roundLosers, matchups

def create_round_playlist(round, database, playlist_name):
    x = spot.create_playlist(playlist_name, client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"])
    song_uris = []
    i = 0.0
    j = 0.0
    print(f"Creating Round {round} Playlist")
    songs_remaining = len(database)
    print(songs_remaining)
    for data in database["id"]:
        completion = j/len(database)*100.0
        song_uris.append(f"spotify:track:{data}")
        i = i+1.0
        #print(f"Adding Songs to Playlist: {completion:.2f}% Complete")
        if i == 100 or i == songs_remaining:
            spot.add_to_playlist(x, client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"], song_uris=song_uris)
            songs_remaining = songs_remaining-i
            print(songs_remaining)
            i = 0.0
            song_uris = []
        j = j+1.0
    print(f"Creation of Round {round} Playlist Complete")
            
def calc_round_zero(initial_length):
    x = 1
    while x < initial_length:
        x = x*2
    x = x/2
    
    return 2*(initial_length-x)

# Setup for SPOTIFY API #
env_dict = rank_help.load_env_variables()

# Setup for Ranking Backend #
currentRound = str(rank_help.read_csv_names())
nextRound = str(rank_help.read_csv_names() + 1)
likedSongs = pd.read_csv('./data/'+currentRound+'_starting.csv', sep=',', header=0)
roundWinners = pd.read_csv('./data/'+currentRound+'_winners.csv', sep=',', header=0)
roundLosers = pd.read_csv('./data/'+currentRound+'_losers.csv', sep=',', header=0)
matchups = pd.read_csv('./data/'+currentRound+'_matchups.csv', sep=',', header=0)
headers = ['Track','Artist','Album','Playlist','Type','ISRC','id']
userInput = ""
round = rank_help.read_csv_names()

while True:
    if len(likedSongs)<=1:
        create_round_playlist(round=round, database=roundWinners, playlist_name=f"Round {round} Winners")
        create_round_playlist(round=round, database=roundLosers, playlist_name=f"Round {round} Losers")
        currentRound, nextRound = create_next_round(likedSongs=likedSongs, matchups=matchups, roundWinners=roundWinners, currentRound=currentRound, nextRound=nextRound, headers=headers)
        print(f"Importing Data for Round {currentRound}")
        likedSongs, roundWinners, roundLosers, matchups = read_current_round(currentRound=currentRound)
        
    if userInput != 'restart':
        topseed, bottomseed = rank_help.select_matchup(currentRound=currentRound, env_dict=env_dict, likedSongs=likedSongs)

    print(f"\nSongs Remaining in Round {currentRound}: {len(likedSongs)}")
    
    userInput = rank_help.get_user_input(topseed=topseed, bottomseed=bottomseed)
    
    userInput, likedSongs, matchups, roundWinners, roundLosers = read_user_input(userInput, likedSongs=likedSongs, matchups=matchups, roundWinners=roundWinners, roundLosers=roundLosers)
    if userInput == "stop":
        break