#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: ./run_summarizer.sh <model> <path_to_epub>"
    echo "Available models: gpt-4, claude-3-sonnet"
    exit 1
fi

MODEL="$1"
EPUB_PATH=$(realpath "$2")
EPUB_FILENAME=$(basename "$EPUB_PATH")
SCRIPT_DIR=$(dirname "$(realpath "$0")")

if [[ "$MODEL" != "gpt-4" && "$MODEL" != "claude-3-sonnet" ]]; then
    echo "Invalid model. Available models: gpt-4, claude-3-sonnet"
    exit 1
fi

docker run -it --rm \
    -v "$SCRIPT_DIR/openai_key.txt:/app/openai_key.txt" \
    -v "$SCRIPT_DIR/anthropic_key.txt:/app/anthropic_key.txt" \
    -v "$EPUB_PATH:/app/$EPUB_FILENAME" \
    -v "$SCRIPT_DIR/summarized:/app/summarized" \
    epub_summarizer \
    python summarize.py "$MODEL" "$EPUB_FILENAME"
