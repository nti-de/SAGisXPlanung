#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <new_version_tag>"
    exit 1
fi

# Extract new version tag from the first argument
new_version="$1"

current_version=$(grep -oP "VERSION\s*=\s*'([^']+)" src/SAGisXPlanung/__init__.py | awk -F"'" '{print $2}')
echo "Current application version: $current_version"

# List of files to update
files=("setup.py" "setup.cfg" "installer/setup.iss" "src/SAGisXPlanung/metadata.txt" "src/SAGisXPlanung/__init__.py")

# Loop through each file and perform version replacement
for file in "${files[@]}"; do
    # Check if the file exists
    if [ ! -f "$file" ]; then
        echo "File not found: $file"
        continue
    fi

    # Perform version replacement using sed
    sed -i "s/\($current_version\)/$new_version/I" "$file"

    # Additional replacements specific to your use case
    # You may add more sed commands as needed for your specific files

    echo "Version in $file updated from $current_version to $new_version"
done

# Rename sql file for database setup
old_sql_file="src/SAGisXPlanung/database/create_v$current_version.sql"
new_sql_file="src/SAGisXPlanung/database/create_v$new_version.sql"

if [ -f "$old_sql_file" ]; then
    git mv "$old_sql_file" "$new_sql_file"
    echo "File $old_sql_file renamed to $new_sql_file"
else
    echo "File $old_sql_file not found. No renaming performed."
    echo "Check if database create script is present."
    exit 1  # Exit with an error code
fi

echo "Version update complete."
