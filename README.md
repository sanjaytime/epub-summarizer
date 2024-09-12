# EPUB Summarizer

This project provides a Python script that generates a chapter-by-chapter summary of an EPUB file using the OpenAI GPT-4 model. The summarizer runs in a Docker container for easy setup and execution.

## Prerequisites

- Docker installed on your system
- An OpenAI API key

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/epub-summarizer.git
   cd epub-summarizer
   ```

2. Create a file named `openai_key.txt` in the project root directory and paste your OpenAI API key into it.

3. Build the Docker image:
   ```
   docker build -t epub-summarizer .
   ```

## Usage

To summarize an EPUB file, use the following command:

```
./run_summarizer.sh /path/to/your/book.epub
```

Replace `/path/to/your/book.epub` with the actual path to your EPUB file.

The script will process the EPUB file chapter by chapter, providing summaries as they are generated. The final summary will be saved in the `summarized` directory with a filename based on the original EPUB file name.

## Output

- The script will display chapter summaries in the console as they are processed.
- A progress bar will show the overall progress of the summarization.
- The final summary will be saved as a Markdown file in the `summarized` directory.

## Notes

- The summarization process may take some time depending on the size of the EPUB file and the number of chapters.
- Ensure that your OpenAI API key has sufficient credits for the summarization task.
- The script uses the GPT-3.5 Turbo model for summarization. You can modify the `summarize_text` function in `summarize_epub.py` to use a different model if desired.

## Troubleshooting

If you encounter any issues, please check the following:

1. Ensure that the `openai_key.txt` file exists and contains a valid API key.
2. Make sure Docker is running on your system.
3. Verify that the EPUB file path is correct and accessible.

For any other problems, please open an issue in the GitHub repository.