#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage:"
    echo "./dupe.sh <filename> <number_of_copies>  # to duplicate"
    echo "./dupe.sh <filename> undo                # to undo duplicates"
    exit 1
fi

# Get the file name and action/number of copies
FILENAME=$1
ACTION=$2

# Get the base name without extension
BASENAME=$(basename "$FILENAME" .svelte)

# Handle duplication
if [[ "$ACTION" =~ ^[0-9]+$ ]]; then
    NUM_COPIES=$ACTION
    for i in $(seq 1 $NUM_COPIES); do
        NEW_FILENAME="${BASENAME}_${i}.svelte"
        cp "$FILENAME" "$NEW_FILENAME"
        echo "Created: $NEW_FILENAME"
    done
    echo "Finished creating $NUM_COPIES copies of $FILENAME."

# Handle removal
elif [ "$ACTION" == "undo" ]; then
    for file in ${BASENAME}_*.svelte; do
        if [ -e "$file" ]; then
            rm "$file"
            echo "Removed: $file"
        else
            echo "No files found matching pattern ${BASENAME}_*.svelte"
            break
        fi
    done
    echo "Finished removing duplicates of $FILENAME."

# Invalid action
else
    echo "Invalid action. Please provide a number to duplicate or 'undo' to delete duplicates."
    exit 1
fi
