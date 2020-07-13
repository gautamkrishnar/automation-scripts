import requests
import json
import hashlib
import pafy
import os
import dropbox
from urllib.parse import quote
import re

#####################
# Global vars
#####################

## Youtube API Key
YT_API_KEY = ""

#####################
# Main code
#####################

def get(url, optional_params = {}):
    """
    Returns the JSON after making the API call to the passed URL
    :param url: (string) API Enpoint URL
    :param optional_params: (dictionary) Optional parameters
    :return: (python dictionary)
    """
    get_params = {"key": YT_API_KEY}
    get_params.update(optional_params)
    # Building URL manually because python params was not working.
    url = url + "?"
    for key in get_params.keys():
        url = url + quote(str(key))+"="+quote(str(get_params[key]))+"&"
    url = url[:-1]
    data = requests.get(url)
    #print(str(data))
    #print(url)
    if data.status_code == 200:
        data = json.loads(data.text)
        return data
    else:
        print("Error in sending request... Status: "+ str(data.status_code))
        print(url)
        return 0

def build_json(channel_url):
    """
    Returns a final json after uploading the video and formatting the urls.
    :param channel_url: Yt channel URL
    :return movies_json: Json with all movies
    """
    counter = 0
    channel_id = str(channel_url.split("/")[-1:][0]) # Getting channel Id
    print("Channel id: "+channel_id)
    print("Getting channel data...")
    channel_data =  get("https://www.googleapis.com/youtube/v3/channels", {"id": channel_id, "part":"contentDetails"})
    # getting uploads playlist id
    print("Getting uploads data...")
    try:
        upload_playlist_id = channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except IndexError:
        print("No uploads found...")
        exit(1)
    movies_json = []
    nextPage = None
    while True:
        if not nextPage:
            # First Page
            tmp_video_json = get("https://www.googleapis.com/youtube/v3/playlistItems", {"playlistId" : upload_playlist_id, "part":"snippet", "maxResults": "50"})
            # if tmp_video_json["pageInfo"]["totalResults"] == 0:
            #     # Has no uploads playlist
            #     playlist_data = get("https://www.googleapis.com/youtube/v3/playlists",{"part": "snippet,contentDetails", "channelId": channel_id , "maxResults": "50"})
            #     upload_playlist_id = playlist_data["items"][0]["id"]
            #     tmp_video_json = get("https://www.googleapis.com/youtube/v3/playlistItems",{"playlistId": upload_playlist_id, "part": "snippet", "maxResults": "50"})
            print("Uploads playlist ID: " + upload_playlist_id)
        else:
            # Second page +++
            tmp_video_json = get("https://www.googleapis.com/youtube/v3/playlistItems", {"playlistId": upload_playlist_id, "part": "snippet", "maxResults": "50", "pageToken" : nextPage})
        yt_local_json = {}
        yt_video_list = tmp_video_json['items']
        for video in yt_video_list:
            yt_local_json = {}
            yt_local_json['showname'] = check_and_get(video["snippet"]["title"]).lower()
            yt_local_json['name'] = check_and_get(video["snippet"]["title"])
            #yt_local_json['thumbnail'] = check_and_get(video["snippet"]["thumbnails"]["high"]["url"])
            yt_local_json['description'] = smart_truncate(check_and_get(video["snippet"]["description"]))
            yt_local_json['long_description'] = check_and_get(video["snippet"]["description"])
            yt_local_json['type'] = "Full Movie"
            #yt_local_json['duration'] = str(135 * (1000 * 60))
            yt_local_json['bcid'] = int(hashlib.sha256(str(video["snippet"]["resourceId"]["videoId"]).encode('utf-8')).hexdigest(),16) % 10 ** 7
            datear = video["snippet"]["publishedAt"][0:10].split("-")
            yt_local_json['showonairdate'] = ((datear[1] + "/" + datear[2] + "/" + datear[0]))
            yt_local_json['poster'] = check_and_get(video["snippet"]["thumbnails"]["high"]["url"]) # Thumbnail
            temp_save_url = "./downloads/" + str(yt_local_json['bcid']) + ".mp4"
            video_url = None
            if not os.path.isfile(temp_save_url):
                    try:
                        video = pafy.new("https://www.youtube.com/watch?v=" + video["snippet"]["resourceId"]["videoId"])
                        streams = video.streams
                        for stream in streams:
                            temp_save_url = "./downloads/" + str(yt_local_json['bcid']) + ".mp4"
                            if stream._extension == 'mp4':
                                if int(stream.quality.split("x")[0]) <= 720:  # 480p (720 � 480)
                                    print("Downloading video for " + str(yt_local_json['name'] + "..."))
                                    # Downloading to local directory
                                    stream.download(temp_save_url, quiet=True)
                                    # Uploading to dropbox
                                    video_url = save_to_dropbox(temp_save_url) or None
                                    break
                            else:
                                continue
                    except:
                        pass
            else:
            ## Getting video URL
                print("File already downloaded locally, getting dropbox URL...")
                video_url = save_to_dropbox(temp_save_url)
            if video_url == None:
                video_url = ""

            # Appending it to Main JSON according to the format
            append_data = {
            "0": yt_local_json,
            "video": [
                {
                    "src": video_url
                },
                {
                    "DRM": "False"
                }
            ]
            }
            movies_json.append(append_data)
            counter = counter + 1
            if counter == 20:
                break
        # Has more videos
        # if 'nextPageToken' in tmp_video_json.keys():
        #     nextPage = tmp_video_json['nextPageToken']
        # else:
        #     #Stopping the execution
        #     break
        break
    return movies_json

def check_and_get(data):
    """
    Used to set empty value to JSON if key doesnt exist in API
    :param data:
    :return:
    """
    if data !=  None:
        return data
    else:
        return ""

def smart_truncate(content, length=160, suffix='.'):
    """
    Returns string
    :param content:
    :param length:
    :param suffix:
    :return:
    """
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix

def fetch_movie_data(channel_url, output_file):
    """
    Gets and write the movie data to output file
    :param channel_url: (string) Youtube channel url
    :param output_file: (string) Output filename
    :return:
    """

    # Building JSON data
    try:
        moviedata_json = build_json(channel_url)
    except KeyboardInterrupt:
        # To save data even if the program is stopped while running
        pass

    # Writing json to the file
    prettyprint(moviedata_json)
    with open(output_file, 'w') as outfile:
        json.dump(moviedata_json, outfile, ensure_ascii=False)
    return

def prettyprint(json_dict):
    """
    function to prettyprint json (For debugging purposes
    :param json_dict: dictionary
    :return:
    """
    print(json.dumps(json_dict, indent=4, sort_keys=True))
    return

def save_to_dropbox(file_from):
    """
    Uploads a file to the dropbox
    :param file_name: (String) Filename to upload
    :return url: (String) URL of the file, or return None
    """
    url = None
    access_token = ''
    dbx = dropbox.Dropbox(access_token)
    upload_path = "/youtube/"+file_from.split("/")[-1:][0]
    try:

        # Checking whether file exists or not
        try:
            dbx.files_get_metadata(upload_path)
            print("File exists in dropbox... Skipping...")
            #url = dbx.sharing_get_shared_links(upload_path).links[0].url
            url = dbx.sharing_list_shared_links(upload_path).links[0].url
            print(url)
            fileExists = True
        except dropbox.exceptions.ApiError:
            fileExists = False
            pass
        # File doesn't exists
        if not fileExists:
            print("Uploading to dropbox...")
            with open(file_from, 'rb') as f:
                dbx.files_upload(f.read(), upload_path)
        if url == None:
            # Getting the shareable link
            url = dbx.sharing_create_shared_link_with_settings(upload_path).url
        # Converting to downloadable link
        url = re.sub(r"\?dl\=0", "?dl=1", url)
        return url
    except ConnectionError:
        print("No internet connection....")
        exit(1)
    except:
        return None


def main():
    # Give channel url here....

    # channel_url = input("Enter the channel URL: ")
    # output_file = input("Enter the file Name: ")
    fetch_movie_data("https://www.youtube.com/channel/UCgdF4GdqtKIHgc3GvSUwH7Q", "English Professionally.json")
    exit()

if __name__ == '__main__':
    main()