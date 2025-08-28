
import base64
import json
from requests import post, get
import time
import pandas as pd

###################################################
# USER AUTHORIZATION
#
#
###################################################
def get_token(client_id, client_secret):
    auth_string = client_id +":"+client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "+auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    
    return token

def get_user_token(client_id, client_secret, user_code, redirect_uri):
    auth_string = client_id +":"+client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "+auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "code": user_code, 
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    result = post(url, headers=headers, data=data)
    if result.status_code != 200:
        print(result.text)
        return False
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    print(json_result["access_token"])
    print(json_result["refresh_token"])
    
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer "+token}
    
def request_user_authorization(client_id, redirect_uri):
    url = "https://accounts.spotify.com/authorize"
    scope = "user-modify-playback-state playlist-modify-public playlist-modify-private user-read-currently-playing"
    headers = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope
    }
    result = get(url, headers=headers)
    print(result)
    json_result = json.loads(result.content)
    print(json_result)

def refresh_user_token(client_id, client_secret, refresh_token):
    auth_string = client_id +":"+client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "Authorization": "Basic "+auth_base64,
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
        
    result = post(url, headers=headers, data=data)
    if(result.status_code != 200):
        response = f"Could not refresh token\nError Code: {result.status_code}"
        print(response+"\n"+result.reason)
        return False
    
    json_result = json.loads(result.content)["access_token"]
    
    return json_result


#############################################################################
# PLAYBACK MANIPULATION
#
#
#
#
#############################################################################
def queue_song(song_id, client_id, client_secret, refresh_token):
    # Request new token for user #
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    while token == False:
        print("Retrying to refresh token in 1 second")
        time.sleep(1)
        token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    
    url = "https://api.spotify.com/v1/me/player/queue"
    track_uri = f"?uri=spotify%3Atrack%3A{song_id}"
    headers = {
        "Authorization": "Bearer "+token
    }
    result = post(url+track_uri, headers=headers)
    
    if(result.status_code != 200):
        print(f"Could not queue song\nError Code {result.status_code}\n{json.loads(result.text).get('error', {}).get('message', result.text)}")

#############################################################################
# PLAYLIST 
#
#
#
#
#############################################################################
def create_playlist(playlist_name, client_id, client_secret, refresh_token):
    user_id = get_user_id(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token).split(":")[2]
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    while token == False:
        print("Retrying to refresh token in 1 second")
        time.sleep(1)
        token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+token
    }
    data = {
        "name": playlist_name,
        "description": "New playlist description"
    }
    result = post(url=url, headers=headers, data=json.dumps(data))
    
    if(result.status_code != 201):
        response = f"Could not create playlist\nError Code {result.status_code}"
        print(response)
        print(result.text)
        return False
    json_result = json.loads(result.content)["uri"].split(":")[2]
    
    return json_result

def add_to_playlist(playlist_id, client_id, client_secret, refresh_token, song_uris):
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": "Bearer "+token,
        "Content-Type": "application/json"
    }
    data = {
        "uris": song_uris
    }
    
    result = post(url=url, headers=headers, data=json.dumps(data))
    
    if(result.status_code != 201):
        response = f"Could not add to playlist\nError Code {result.status_code}"
        print(response)
        print(result.text)
        return False
    
    return True

def get_user_playlists(env_dict, limit, offset, url=None):
    client_id = env_dict["client_id"]
    client_secret = env_dict["client_secret"]
    refresh_token = env_dict["refresh_token"]
    user_id = get_user_id(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token).split(":")[2]
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    
    while token == False:
        print("Retrying to refresh token in 1 second")
        time.sleep(1)
        token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
        
    if url == None:
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists?limit={limit}&offset={offset}"
        
    headers = {
        "Authorization": "Bearer "+token
    }
    
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
        
    return json_result

def get_all_user_playlists(env_dict, limit, offset):
    print(f"Downloading User Playlist Data\n")
    result = get_user_playlists(env_dict=env_dict, limit=limit, offset=offset)
    data = []
    iteration = 0;
    total_playlists = result['total']
    
    for playlist in result['items']:
        data.append({
            'name': playlist.get('name'),
            'id': playlist.get('id')
        })
        print_progress_bar(iteration=iteration, total=total_playlists)
        iteration = iteration + 1
        
    while result['next'] != None:
        result = get_user_playlists(env_dict=env_dict, limit=limit, offset=offset, url=result['next'])
        for playlist in result['items']:
            data.append({
                'name': playlist.get('name'),
                'id': playlist.get('id')
            })
            print_progress_bar(iteration=iteration, total=total_playlists)
            
            iteration = iteration + 1
    print("\n")
    df = pd.DataFrame(data)
    return df

def get_songs_in_playlist(env_dict, playlist_id):
    client_id = env_dict["client_id"]
    client_secret = env_dict["client_secret"]
    refresh_token = env_dict["refresh_token"]
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    
    while token == False:
        print("Retrying to refresh token in 1 second")
        time.sleep(1)
        token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
        
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        
    headers = {
        "Authorization": "Bearer "+token
    }
    
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    total_tracks = json_result['total']
    iteration = 0;
    data = []
    for item in json_result['items']:
        iteration = iteration + 1
        print_progress_bar(iteration=iteration, total=total_tracks)
        data.append({
            'Track': item.get('track').get('name'),
            'Artist': item.get('track').get('artists')[0].get('name'),
            'Album': item.get('track').get('album').get('name'),
            'id': item.get('track').get('id'),
            'added_by': item.get('added_by').get('id')
        })
    
    while json_result['next'] != None:
        result = get(json_result['next'], headers=headers)
        json_result = json.loads(result.content)
        
        for item in json_result['items']:
            iteration = iteration + 1
            print_progress_bar(iteration=iteration, total=total_tracks)
            data.append({
                'Track': item.get('track').get('name'),
                'Artist': item.get('track').get('artists')[0].get('name'),
                'Album': item.get('track').get('album').get('name'),
                'id': item.get('track').get('id'),
                'added_by': item.get('added_by').get('id')
            })
            
        
    
    df = pd.DataFrame(data)
    return df
    
    
    
#############################################################################
# SPOTIFY SEARCH
#
#
#
#
#############################################################################
def get_user_id(client_id, client_secret, refresh_token):
    token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    while token == False:
        print("Retrying to refresh token in 1 second")
        time.sleep(1)
        token = refresh_user_token(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
    
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": "Bearer "+token
    }
    result = get(url, headers=headers)
    
    if(result.status_code != 200):
        response = f"Could not queue song\nError Code {result.status_code}"
        print(response)
        return 0
    
    json_result = json.loads(result.content)["uri"]
    return json_result

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    
    query = f"?q={artist_name}&type=artist&limit=1"
    
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    
    if len(json_result) == 0:
        print("No Artist Found")
        return None
    
    return json_result[0]

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    
    return json_result

#############################################################################
# HELPER FUNCTIONS
#
#
#
#
#############################################################################
def print_progress_bar(iteration, total, length=40):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\rProgress: |{bar}| {percent}% Complete', end='\r')
    
    if iteration == total:
        print()
        
    time.sleep(0.02)