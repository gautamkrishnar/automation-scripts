YT_API_KEY="" # get from https://developers.google.com/youtube/v3/getting-started
PLAYLIST_ID="" # Playlist id of the channel's uploads playlist. For this you need to do https://stackoverflow.com/a/46169886

while true; do
    VIDEO_API_DATA=$(curl -s "https://www.googleapis.com/youtube/v3/playlistItems?playlistId=${PLAYLIST_ID}&part=snippet&maxResults=1&key=${YT_API_KEY}")
    VIDEO_ID=$(echo "$VIDEO_API_DATA" | jq -r ".items[0].snippet.resourceId.videoId")
    VIDEO='https://www.youtube.com/watch?v='$VIDEO_ID

    if [[ ! -z "$VIDEO_ID" ]]; then
        THUMBNAIL_URL=$(echo "$VIDEO_API_DATA" | jq -r ".items[0].snippet.thumbnails.default.url")
        if [[ $THUMBNAIL_URL == *"_live"* ]]; then
            if ! compgen -G "*${VIDEO_ID}*" > /dev/null; then
                echo "New Live Stream: $VIDEO"
                yt-dlp -f --live-from-start -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" "$VIDEO"
            fi
        fi
    else
        echo "No video ID found."
    fi
    sleep 15
done