# EPUB Summarizer

This tool summarizes EPUB books chapter by chapter using OpenAI’s GPT-3.5 API. Summaries are saved in a markdown file under a `summarized/` directory.

## Prerequisites

- Docker
- OpenAI API Key

## Setup

1. Clone this repository.
2. Install Docker if you haven't already.
3. Create a file `openai_key.txt` in the project root and store your OpenAI API key in it:
    ```bash
    echo "sk-your-openai-api-key" > openai_key.txt
    ```

4. Build the Docker image:
    ```bash
    docker build -t epub_summarizer .
    ```

## Usage

To summarize an EPUB file:

```bash
./run_summarizer.sh <path_to_epub_file>
