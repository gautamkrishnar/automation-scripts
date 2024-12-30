# NTFS Filename Cleaner and Renamer

This script renames files in the current directory by cleaning up invalid characters and ensuring the filenames are compatible with Windows NTFS file systems. It also ensures filenames do not exceed the 255-character limit (including file extensions) imposed by NTFS.

## Features
- **Cleans invalid characters**: Removes characters not supported by NTFS (`\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|`), as well as non-ASCII characters (including emojis).
- **Filename length enforcement**: Truncates filenames to ensure they do not exceed the **255-character** limit, preserving the file extension.