import sys
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import openai
import re
import logging
from tqdm import tqdm  # For progress bar

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to split text into chunks that fit within the token limit
def split_text_into_chunks(text, max_tokens_per_chunk=3500):
    words = text.split()
    chunks = []
    chunk = []
    
    for word in words:
        chunk.append(word)
        if len(chunk) >= max_tokens_per_chunk:
            chunks.append(" ".join(chunk))
            chunk = []
    
    if chunk:
        chunks.append(" ".join(chunk))
    
    return chunks

# Function to extract text and chapter titles from the epub file
def extract_chapters_from_epub(epub_file):
    book = epub.read_epub(epub_file)
    chapters = []

    # Loop through all items in the book
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')

            # Try to extract a chapter title if available
            chapter_title = soup.find('h1') or soup.find('h2') or soup.find('h3')  # Common header tags for chapter titles
            chapter_title = chapter_title.get_text() if chapter_title else None

            # Extract chapter text
            clean_text = soup.get_text()
            clean_text = re.sub(r'\s+', ' ', clean_text)  # Remove excess whitespace

            chapters.append({
                'title': chapter_title if chapter_title else f"Chapter {len(chapters) + 1}",
                'text': clean_text
            })

    return chapters

# Improved prompt to get more focused, detailed summaries
def generate_summary_prompt(chapter_title, chapter_text):
    return f"""
    You are an expert book summarizer. Your job is to summarize books accurately and concisely.

    Here is a chapter titled '{chapter_title}' from an EPUB book. Please provide a detailed summary of this chapter, focusing on:
    - The key points and major themes
    - Important events or concepts discussed
    - The overall structure of the chapter
    Keep your summary clear and concise, but make sure it covers the essential content.
    """

# Function to generate summary using OpenAI API
def generate_summary(api_key, chapter_title, text, max_tokens=300):
    openai.api_key = api_key
    
    # Split the text into smaller chunks if necessary
    text_chunks = split_text_into_chunks(text)
    final_summary = []

    for chunk in text_chunks:
        prompt = generate_summary_prompt(chapter_title, chunk)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional book summarizer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        final_summary.append(response['choices'][0]['message']['content'])
    
    return " ".join(final_summary)

# Function to save summary to markdown file
def save_summary_to_markdown(epub_file, summaries):
    # Create the 'summarized' directory if it doesn't exist
    if not os.path.exists('summarized'):
        os.makedirs('summarized')

    # Create the markdown filename based on the epub file
    base_filename = os.path.basename(epub_file).replace('.epub', '')
    markdown_filename = f'summarized/{base_filename}_summary.md'

    # Write the summary to the markdown file
    with open(markdown_filename, 'w') as md_file:
        md_file.write("# Summary of {}\n\n".format(base_filename))
        for i, summary in enumerate(summaries, 1):
            md_file.write(f"## {summary['title']}\n\n")
            md_file.write(summary['content'] + "\n\n")

    logging.info(f"Summary saved to {markdown_filename}")

# Function to display summaries with better formatting in CLI
def display_formatted_summary(chapter_title, summary):
    print(f"\n{'-'*50}")
    print(f"{chapter_title} Summary:\n")
    print(summary)
    print(f"{'-'*50}\n")

# Main function to summarize chapters from EPUB
def summarize_epub_chapter_by_chapter(epub_file, api_key):
    logging.info("Extracting chapters from the EPUB file...")
    
    # Extract chapters from the EPUB
    chapters = extract_chapters_from_epub(epub_file)
    summaries = []

    logging.info(f"Total chapters found: {len(chapters)}")

    # Summarize each chapter and log progress
    for i, chapter in enumerate(tqdm(chapters, desc="Summarizing chapters", leave=False, ncols=100), 1):
        chapter_title = chapter['title']
        chapter_text = chapter['text']

        logging.info(f"Summarizing {chapter_title}...")
        summary = generate_summary(api_key, chapter_title, chapter_text)

        # Display summary in formatted CLI
        display_formatted_summary(chapter_title, summary)
        
        summaries.append({'title': chapter_title, 'content': summary})

    # Save the summary to a markdown file
    save_summary_to_markdown(epub_file, summaries)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <epub_file>")
        sys.exit(1)
    
    epub_file_path = sys.argv[1]

    # Read the API key from the file
    with open("openai_key.txt", "r") as f:
        openai_api_key = f.read().strip()
    
    # Summarize the EPUB chapter by chapter
    summarize_epub_chapter_by_chapter(epub_file_path, openai_api_key)
