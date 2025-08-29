import pandas as pd
import os
import spotify_helpers as spot
import ranking_helpers as rank_help

def save_choice(likedSongs, matchups, roundWinners, roundLosers, playlist_name):
    likedSongs.to_csv(f'./data/rankings/{playlist_name}/{currentRound}_starting.csv', index=False)
    roundWinners.to_csv(f'./data/rankings/{playlist_name}/{currentRound}_winners.csv', index=False)
    roundLosers.to_csv(f'./data/rankings/{playlist_name}/{currentRound}_losers.csv', index=False)
    matchups.to_csv(f'./data/rankings/{playlist_name}/{currentRound}_matchups.csv', index=False)
        
def is_integer(input_string):
    try: 
        int(input_string)
        return True
    except ValueError:
        return False

def read_user_input(input, likedSongs, matchups, roundWinners, roundLosers, playlist_name):
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
        save_choice(likedSongs=likedSongs, matchups=matchups, roundWinners=roundWinners, roundLosers=roundLosers, playlist_name=playlist_name)
        
    return input, likedSongs, matchups, roundWinners, roundLosers
        
def create_next_round(starting, round, headers, playlist_name, winners=None):
    if not os.path.isdir(f'./data/rankings/{playlist_name}'):
        os.makedirs(f'./data/rankings/{playlist_name}', exist_ok=True)
        
    print(f"\nCreating files for Round {round}")
    starting.to_csv(f'./data/rankings/{playlist_name}/{round}_starting.csv', index=False)
    starting.to_csv(f'./data/backup/{playlist_name}_{round}_startingbackup.csv', index=False)
    pd.DataFrame(columns=headers).to_csv(f'./data/rankings/{playlist_name}/{round}_losers.csv', index=False)
    pd.DataFrame(columns=headers).to_csv(f'./data/rankings/{playlist_name}/{round}_matchups.csv', index=False)
    
    # Create blank winner .csv if df is not specified
    # this is really only used for the initial db creation
    if not isinstance(winners, pd.DataFrame):
        pd.DataFrame(columns=headers).to_csv(f'./data/rankings/{playlist_name}/{round}_winners.csv', index=False)
    else:
        winners.to_csv(f'./data/rankings/{playlist_name}/{round}_winners.csv', index=False)
    
    print(f"Welcome to round {round}!\n")
    return str(round), str(round+1)

def read_current_round(round, playlist_name):
    likedSongs = pd.read_csv(f'./data/rankings/{playlist_name}/{round}_starting.csv', sep=',', header=0)
    roundWinners = pd.read_csv(f'./data/rankings/{playlist_name}/{round}_winners.csv', sep=',', header=0)
    roundLosers = pd.read_csv(f'./data/rankings/{playlist_name}/{round}_losers.csv', sep=',', header=0)
    matchups = pd.read_csv(f'./data/rankings/{playlist_name}/{round}_matchups.csv', sep=',', header=0)
    
    return likedSongs, roundWinners, roundLosers, matchups

def create_round_playlist(database, name):
    x = spot.create_playlist(name, client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"])
    song_uris = []
    i = 0.0
    j=0.0
    print(f"Creating {name} Playlist")
    songs_remaining = len(database)
    for data in database["id"]:
        song_uris.append(f"spotify:track:{data}")
        i = i+1.0
        if i == 100 or i == songs_remaining:
            spot.add_to_playlist(x, client_id=env_dict["client_id"], client_secret=env_dict["client_secret"], refresh_token=env_dict["refresh_token"], song_uris=song_uris)
            songs_remaining = songs_remaining-i
            i = 0.0
            song_uris = []
        spot.print_progress_bar(iteration=j, total=len(database))
        j = j+1
    spot.print_progress_bar(iteration=len(database), total=len(database))

def determine_folders():
    folders = [f for f in os.listdir('./data/rankings') if os.path.isdir(os.path.join('./data/rankings', f))]
    if folders:
        return True
    return False

def create_calibration_round(env_dict):
    response = spot.get_all_user_playlists(env_dict=env_dict, limit=10, offset=0)

    for index, row in response.iterrows():
        print(f"{index} -- {row.to_dict()['name']}")
    
    userInput = int(input("Please select a Playlist for Ranking >>>: "))
    playlist_name = response.iloc[userInput]['name']
    print(f"Downloading Song Data from: {playlist_name}")
    initial_data = spot.get_songs_in_playlist(env_dict=env_dict, playlist_id=response.iloc[userInput]['id'])
    initial_data = initial_data.sort_values(by='Track')
    
    # Remove tracks without a valid ID
    initial_data = initial_data[initial_data['id'].notna() & (initial_data['id'] != '')]
    # Remove duplicate tracks by the same artist #
    initial_data = initial_data.drop_duplicates(subset=["Track", "Artist"], keep='first')
    
    # Creating Calibration Round
    offset_val = len(initial_data)-rank_help.prev_power_of_two(len(initial_data))
    skip_amount = len(initial_data)-(2*offset_val)
    skip_db = initial_data.sample(n=skip_amount).sort_values(by="Track")
    initial_data = initial_data[~initial_data['id'].isin(skip_db['id'])]
    
    create_next_round(starting=initial_data, round=0, headers=headers, winners=skip_db, playlist_name=playlist_name)
    
    return playlist_name
    

# # Setup for SPOTIFY API #
env_dict = rank_help.load_env_variables()
headers = ['Track','Artist','Album','id','added_by']
playlist_name = ''

# First Run
if determine_folders() == False:
    playlist_name = create_calibration_round(env_dict=env_dict)
else:
    folders = [f for f in os.listdir('./data/rankings') if os.path.isdir(os.path.join('./data/rankings', f))]
    print(folders)
    print(f"Please select a Playlist to Rank")
    print(f"{0} -- New Ranking")
    for idx, folder in enumerate(folders):
        print(f"{idx+1} -- {folder}")
    ranking_select = int(input(">>>> "))
    if ranking_select == 0:
        playlist_name = create_calibration_round(env_dict=env_dict)
    else:
        playlist_name = folders[ranking_select-1]
    
#Setup for Ranking Backend #
currentRound = str(rank_help.read_csv_names())
nextRound = str(rank_help.read_csv_names() + 1)
likedSongs, roundWinners, roundLosers, matchups = read_current_round(round=currentRound, playlist_name=playlist_name)
userInput = ""

while True:
    if len(likedSongs)<=1:
        create_round_playlist(database=roundWinners, name=f"{playlist_name} Round {currentRound} Winners")
        create_round_playlist(database=roundLosers, name=f"{playlist_name} Round {currentRound} Losers")
        currentRound, nextRound = create_next_round(starting=roundWinners, round=int(nextRound), headers=headers, playlist_name=playlist_name)
        print(f"Importing Data for Round {currentRound}")
        likedSongs, roundWinners, roundLosers, matchups = read_current_round(round=currentRound, playlist_name=playlist_name)
        
    if userInput != 'restart':
        topseed, bottomseed = rank_help.select_matchup(currentRound=currentRound, env_dict=env_dict, likedSongs=likedSongs)

    print(f"\nSongs Remaining in Round {currentRound}: {len(likedSongs)}")
    
    userInput = rank_help.get_user_input(topseed=topseed, bottomseed=bottomseed)
    
    userInput, likedSongs, matchups, roundWinners, roundLosers = read_user_input(userInput, likedSongs=likedSongs, matchups=matchups, roundWinners=roundWinners, roundLosers=roundLosers, playlist_name=playlist_name)
    if userInput == "stop":
        break
