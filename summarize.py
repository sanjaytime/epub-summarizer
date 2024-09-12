import sys
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import openai
from anthropic import Anthropic
import time
import colorama
import logging
import threading
from itertools import cycle

colorama.init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def spinner_animation():
    return cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])

def retry_animation():
    return cycle(['◐', '◓', '◑', '◒'])

def display_animation(stop_event, message, animation):
    spinner = animation()
    while not stop_event.is_set():
        sys.stdout.write(f"\r{colorama.Fore.CYAN}{next(spinner)} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(message) + 2) + '\r')
    sys.stdout.flush()

def clean_text(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text().strip()

def summarize_text(text, api_key, model, max_bullets=3, max_retries=5):
    if not text:
        return "This chapter appears to be empty."

    for attempt in range(max_retries):
        try:
            if model == 'gpt-4':
                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"You are a helpful assistant that summarizes text. Provide summaries in {max_bullets} bullet points max, being as concise as possible."},
                        {"role": "user", "content": f"Please summarize the following text in {max_bullets} bullet points max:\n\n{text}"}
                    ]
                )
                return response.choices[0].message['content']
            elif model == 'claude-3-sonnet':
                client = Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": f"You are a helpful assistant that summarizes text. Provide summaries in {max_bullets} bullet points max, being as concise as possible. Please summarize the following text in {max_bullets} bullet points max:\n\n{text}"}
                    ]
                )
                return message.content[0].text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff
                stop_event = threading.Event()
                retry_message = f"Error occurred. Retry attempt {attempt + 1}/{max_retries}"
                retry_thread = threading.Thread(target=display_animation, args=(stop_event, retry_message, retry_animation))
                retry_thread.start()
                time.sleep(wait_time)
                stop_event.set()
                retry_thread.join()
            else:
                logging.error(f"Error after {max_retries} attempts: {str(e)}")
                return f"Error summarizing text: {str(e)}"

def get_chapter_title(chapter):
    soup = BeautifulSoup(chapter.get_content(), 'html.parser')
    title = soup.find('title')
    if title:
        return title.text.strip()
    h1 = soup.find('h1')
    if h1:
        return h1.text.strip()
    return "Untitled Chapter"

def process_epub(epub_path, api_key, model):
    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)

    summaries = []
    total_tokens = 0

    logging.info(f"Found {len(chapters)} chapters")
    print(f"{colorama.Fore.CYAN}Summarizing {len(chapters)} chapters:")

    for i, chapter in enumerate(chapters):
        chapter_title = get_chapter_title(chapter)
        content = clean_text(chapter.get_content().decode('utf-8'))
        logging.info(f"Processing chapter {i+1}: {chapter_title}, content length: {len(content)}")

        stop_event = threading.Event()
        spinner_message = f"Processing chapter {i+1}/{len(chapters)}: {chapter_title}"
        spinner_thread = threading.Thread(target=display_animation, args=(stop_event, spinner_message, spinner_animation))
        spinner_thread.start()

        try:
            summary = summarize_text(content, api_key, model)
            total_tokens += len(content.split()) + len(summary.split())

            stop_event.set()
            spinner_thread.join()

            summaries.append(f"## Chapter {i+1}: {chapter_title}\n\n{summary}\n")

            print(f"{colorama.Fore.GREEN}[{i+1}/{len(chapters)}] {chapter_title} - Summarized")
            print(f"{colorama.Fore.YELLOW}{summary}")

            if i < len(chapters) - 1:
                print(f"\n{colorama.Fore.MAGENTA}Processing next chapter...")
                time.sleep(2)  # Pause to show the summary before moving to the next chapter
                print("\033[A" * (summary.count('\n') + 4))  # Move cursor up to overwrite the summary
        except KeyboardInterrupt:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{colorama.Fore.YELLOW}Process interrupted by user. Saving progress...")
            break
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            logging.error(f"Error processing chapter {i+1}: {str(e)}")
            summaries.append(f"## Chapter {i+1}: {chapter_title}\n\nError processing this chapter: {str(e)}\n")

    return summaries, total_tokens

def create_book_summary(summaries, api_key, model):
    combined_summary = "\n".join(summaries)
    prompt = """You are Atlas, an expert in reading and understanding books with 20 years of experience. Your task is to provide a comprehensive summary of the book based on the following chapter summaries. Assume the reader is interested in a "Deep Concept Summary". Format your summary using bullet points for key ideas and tables to highlight key concepts. Include implementable takeaways from the book. After the summary, provide a formatted list of topics you can go in-depth into. Use markdown format for your response.

Here are the chapter summaries:

{combined_summary}

Please provide:
1. A deep concept summary of the book
2. Key ideas in bullet points
3. A table of key concepts
4. Implementable takeaways
5. A list of topics for further exploration
"""

    try:
        return summarize_text(prompt, api_key, model, max_bullets=None)
    except Exception as e:
        logging.error(f"Error in create_book_summary: {str(e)}")
        return f"Error creating book summary: {str(e)}\n\n"

def save_summary(book_summary, summaries, epub_path, total_tokens, model):
    base_name = os.path.splitext(os.path.basename(epub_path))[0]
    output_dir = "summarized"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}_summary.md")

    if model == 'gpt-4':
        estimated_cost = (total_tokens / 1000) * 0.06  # $0.06 per 1K tokens for GPT-4
    elif model == 'claude-3-sonnet':
        estimated_cost = (total_tokens / 1000) * 0.03  # $0.03 per 1K tokens for Claude 3 Sonnet (estimated)

    with open(output_path, 'w') as f:
        f.write(f"# Book Summary for {base_name}\n\n")
        f.write(f"Generated using {model}\n\n")
        f.write(f"Estimated cost: ${estimated_cost:.2f}\n\n")
        f.write(book_summary)
        f.write("\n\n# Chapter Summaries\n\n")
        for summary in summaries:
            f.write(summary)

    print(f"\n{colorama.Fore.GREEN}Summary saved to: {output_path}")
    print(f"{colorama.Fore.YELLOW}Estimated cost: ${estimated_cost:.2f}")

def main():
    if len(sys.argv) != 3:
        print(f"{colorama.Fore.RED}Usage: python summarize.py <model> <path_to_epub>")
        print(f"{colorama.Fore.RED}Available models: gpt-4, claude-3-sonnet")
        sys.exit(1)

    model = sys.argv[1]
    epub_path = sys.argv[2]

    if model not in ['gpt-4', 'claude-3-sonnet']:
        print(f"{colorama.Fore.RED}Invalid model. Available models: gpt-4, claude-3-sonnet")
        sys.exit(1)

    try:
        if model == 'gpt-4':
            with open('openai_key.txt', 'r') as f:
                api_key = f.read().strip()
        elif model == 'claude-3-sonnet':
            with open('anthropic_key.txt', 'r') as f:
                api_key = f.read().strip()
    except FileNotFoundError:
        print(f"{colorama.Fore.RED}Error: API key file not found. Please create the appropriate key file.")
        sys.exit(1)

    try:
        summaries, total_tokens = process_epub(epub_path, api_key, model)
        book_summary = create_book_summary(summaries, api_key, model)
        save_summary(book_summary, summaries, epub_path, total_tokens, model)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"{colorama.Fore.RED}An error occurred. Please check the logs for more information.")

if __name__ == "__main__":
    main()
