import requests
import json
import hashlib
import pafy
import os
import dropbox
import re

#####################
# Global vars
#####################

# API Key global var
API_KEY = ""

#API Read Access Token global var
READ_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NGFhN2E0NDBlMTI0N2NiMmU4OTBhMWYxMmNhZGE5YSIsInN1YiI6IjU5YzBjNTQxOTI1MTQxN2RjMzAwZGFlMiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.G-W-nBqjU4XgZoCYB9SoeP8sgl7RutaeH8GWGXL5Qug"

# Dictionary to store API Endpoints, Just pass this as args to functions.
moviedb_list =   {
    "latest" : "https://api.themoviedb.org/3/movie/latest",
    "now_playing" : "https://api.themoviedb.org/3/movie/now_playing",
    "popular" : "https://api.themoviedb.org/3/movie/popular",
    "top_rated" : "https://api.themoviedb.org/3/movie/top_rated",
    "upcoming" : "https://api.themoviedb.org/3/movie/upcoming",
    "genre_list" : "https://api.themoviedb.org/3/genre/movie/list"
}


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
    get_params = {"api_key": API_KEY}
    get_params.update(optional_params)
    data = requests.request("GET", url, data=get_params)
    if data.status_code == 200:
        data = json.loads(data.text)
        return data
    else:
        print("Error in sending request... Status: "+ str(data.status_code))
        exit(1)

def build_json(url):
    """
    Returns a final json after uploading the video and formatting the urls.
    :param moviedata: (Dictionary) Fetched movie data
    :return movies_json: Json with all movies
    """
    counter = 0
    moviedata = get(url)
    movies_json = []
    max_pages = moviedata['total_pages'] # Total number of pages available
    moviedata = moviedata['results']

    # Fetches all pages
    for i in range(2,max_pages+1):
        temp_data = get(url, {"page": i})['results']
        for movie in temp_data:
            moviedata.append(movie)

    # Process the current page
    for movie in moviedata:
        movie = get('https://api.themoviedb.org/3/movie/'+str(movie['id'])) # Getting more deatails
        movie_local_json = {} # temp var
        movie_local_json['episodenumber'] = ""
        if movie['poster_path'] != None:
            movie_local_json['thumbnail'] = 'https://image.tmdb.org/t/p/w640' + movie['poster_path']  # Poster
        else:
            movie_local_json['thumbnail'] = ""
        movie_local_json['description'] = smart_truncate(check_and_get(movie['overview']))
        movie_local_json['long_description'] = check_and_get(movie['overview'])
        movie_local_json['type'] = "Full Movie"
        movie_local_json['duration'] = str(135 * (1000*60))
        cast = get('https://api.themoviedb.org/3/movie/'+str(movie['id'])+'/credits')
        caststr = ""
        for c in cast['cast']:
            if "department" in c.keys():
                pass
            else:
                caststr+= c['name'] + ' as ' + c['character'] + ','
        caststr = caststr[:-1] or ""
        movie_local_json['cast'] = caststr
        movie_local_json['showname'] = check_and_get(movie['original_title']).lower()
        movie_local_json['bcid'] = int(hashlib.sha256(str(movie['id']).encode('utf-8')).hexdigest(), 16) % 10**7 #Hashing
        genrestr = ""
        for genre in movie['genres']:
            # ToDo: Add genre Names if needed
            genrestr = genrestr + genre['name'] + ","
        genrestr = genrestr[:-1] or ""
        movie_local_json['genre'] = genrestr
        movie_local_json['name'] = check_and_get(movie['original_title'])
        try:
            datear = movie['release_date'].split("-") or ""
            movie_local_json['showonairdate'] = ((datear[1]+"/"+datear[2]+"/"+datear[0]))
        except:
            movie_local_json['showonairdate'] = ""

        if movie['backdrop_path'] != None:
            movie_local_json['poster'] = 'https://image.tmdb.org/t/p/w640' + movie['backdrop_path'] # Thumbnail
        else:
            movie_local_json['poster'] = ""
        print("\n\nFetched "+movie_local_json['name']+" ("+ str(counter+1) +" / " + str(len(moviedata)) + ")")

        # Downloading video to local folder
        temp_save_url = "./downloads/" + str(movie['id']) + ".mp4"
        video_url = None
        if not os.path.isfile(temp_save_url):
            video_list =  get("https://api.themoviedb.org/3/movie/"+str(movie['id'])+"/videos")['results'] or {}
            for video in video_list:
                if "YouTube" in video.values():
                    try:
                        if video['key'].find("youtu.be") != -1:
                            video = pafy.new("https://www.youtube.com/watch?v=" + video['key'].split("/")[-1:][0])
                        else:
                            video = pafy.new("https://www.youtube.com/watch?v=" + video['key'])
                        streams = video.streams
                        for stream in streams:
                            temp_save_url = "./downloads/" + str(movie['id']) + ".mp4"
                            if stream._extension == 'mp4':
                                if int(stream.quality.split("x")[0])<=720: # 480p (720 × 480)
                                    print("Downloading video for "+str(movie['title']+"..."))
                                    # Downloading to local directory
                                    stream.download(temp_save_url, quiet=True)
                                    # Uploading to dropbox
                                    video_url = save_to_dropbox(temp_save_url) or None
                                    break
                            else:
                                continue
                        break
                    except:
                        pass
        else:
            ## Getting video URL
            video_url = save_to_dropbox(temp_save_url)
        if video_url == None:
            video_url = ""
        movie_local_json["languages"] =  check_and_get(movie['original_language'])

        # Appending it to Main JSON according to the format
        append_data = {
            str(counter) : movie_local_json,
            "video" : [
                {
                    "src" : video_url
                },
                {
                    "DRM": "False"
                }
            ]
        }
        movies_json.append(append_data)
        counter =  counter +1
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

def fetch_movie_data(url, output_file):
    """
    Gets and write the movie data to output file
    :param url: (string) API Enpoint URL
    :param output_file: (string) Output filename
    :return:
    """

    # Building JSON data
    try:
        moviedata_json = build_json(url)
    except KeyboardInterrupt:
        # To save data even if the program is stopped while running
        pass

    # Writing json to the file
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
    access_token = 'KUg07hyVM4AAAAAAAAAAD5htp5k8Yrnl-i4SgyrJ8NrDdC6nKfsvcyHG7euL1VKo'
    dbx = dropbox.Dropbox(access_token)
    upload_path = "/"+file_from.split("/")[-1:][0]
    try:

        # Checking whether file exists or not
        try:
            dbx.files_get_metadata(upload_path)
            print("File exists in dropbox... Skipping...")
            url = dbx.sharing_get_shared_links(upload_path).links[0].url
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
    # print("Fetching genres...")
    # global genere_list
    # genre_list = get(moviedb_list['genre_list'])['genres']
    print("Fetching the upcoming movies data...")
    fetch_movie_data(moviedb_list['upcoming'], "output.json")

    exit()

if __name__ == '__main__':
    main()