#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: ./run_summarizer.sh <path_to_epub>"
    exit 1
fi

EPUB_PATH=$(realpath "$1")
EPUB_FILENAME=$(basename "$EPUB_PATH")
SCRIPT_DIR=$(dirname "$(realpath "$0")")

docker run -it --rm \
    -v "$SCRIPT_DIR/openai_key.txt:/app/openai_key.txt" \
    -v "$EPUB_PATH:/app/input.epub" \
    -v "$SCRIPT_DIR/summarized:/app/summarized" \
    epub_summarizer \
    python summarize.py "input.epub"
