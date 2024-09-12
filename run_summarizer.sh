#!/bin/bash

# Check if the required parameter is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: ./run_summarizer.sh <path_to_epub_file>"
    exit 1
fi

EPUB_FILE=$1

# Run the docker container interactively and pass the EPUB file
docker run -it --rm \
    -v "$(pwd)":/app \
    epub_summarizer python summarize.py /app/"$EPUB_FILE"
