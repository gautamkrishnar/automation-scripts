#!/bin/bash

# Function to clean a filename
clean_filename() {
    local filename="$1"
    
    # Remove non-ASCII characters (including emojis)
    filename=$(echo "$filename" | iconv -f utf-8 -t ascii//TRANSLIT)

    # Replace any invalid characters with underscores
    filename=$(echo "$filename" | sed 's/[\\/*?:"<>|]/_/g')

    # Remove leading/trailing spaces
    filename=$(echo "$filename" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # If the filename becomes empty after cleaning, return "Unnamed_File"
    if [ -z "$filename" ]; then
        filename="Unnamed_File"
    fi

    # Truncate filename to 255 characters if necessary, preserving the extension
    # Get the file extension (if any)
    extension="${filename##*.}"
    base_filename="${filename%.*}"

    # If extension exists, preserve it while truncating the base filename
    if [ "$base_filename" != "$filename" ]; then
        # Max length allowed for the base filename (255 minus extension length and dot)
        max_base_length=$((255 - ${#extension} - 1))
        if [ ${#base_filename} -gt $max_base_length ]; then
            filename="${base_filename:0:$max_base_length}.$extension"
        fi
    else
        # If there's no extension, truncate the whole filename to 255 characters
        filename="${filename:0:255}"
    fi

    echo "$filename"
}

# Function to generate a unique filename if a conflict occurs
generate_unique_filename() {
    local base_filename="$1"
    local extension="$2"
    local counter=1
    local new_filename="${base_filename}_${counter}"

    # Ensure the filename is unique by checking if it already exists
    while [ -e "$new_filename.$extension" ]; do
        counter=$((counter + 1))
        new_filename="${base_filename}_${counter}"
    done

    # Return the unique filename with extension
    echo "$new_filename.$extension"
}

# Loop through all files in the current directory
for filepath in *; do
    # Only process files (ignore directories)
    if [ -f "$filepath" ]; then
        # Get the filename without the path
        filename=$(basename "$filepath")
        
        # Clean the filename
        new_filename=$(clean_filename "$filename")
        
        # Check if the cleaned filename is the same as the original one
        if [ "$new_filename" != "$filename" ]; then
            # Check for filename conflict (if file already exists with the new name)
            extension="${new_filename##*.}"
            base_filename="${new_filename%.*}"
            
            # If the file already exists, generate a unique name
            if [ -e "$new_filename" ]; then
                new_filename=$(generate_unique_filename "$base_filename" "$extension")
            fi
            
            # Rename the file
            mv "$filepath" "$new_filename"
            echo "Renamed: '$filename' -> '$new_filename'"
        fi
    fi
done