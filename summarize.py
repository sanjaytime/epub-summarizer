import sys
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import openai
from tqdm import tqdm
import time
import markdown
import colorama
import logging
from itertools import cycle
import threading

colorama.init()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def spinner():
    return cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])

def loading_animation(stop_event):
    spin = spinner()
    while not stop_event.is_set():
        sys.stdout.write(next(spin))
        sys.stdout.flush()
        sys.stdout.write('\b')
        time.sleep(0.1)

def clean_text(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text().strip()

def summarize_text(text, api_key):
    if not text:
        return "This chapter appears to be empty."
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text. Provide summaries in bullet points."},
                {"role": "user", "content": f"Please summarize the following text in bullet points:\n\n{text}"}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Error in summarize_text: {str(e)}")
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

def process_epub(epub_path, api_key):
    book = epub.read_epub(epub_path)
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)
    
    summaries = []
    total_tokens = 0
    
    logging.info(f"Found {len(chapters)} chapters")
    print(colorama.Fore.CYAN + f"Summarizing {len(chapters)} chapters:" + colorama.Fore.RESET)
    
    for i, chapter in enumerate(tqdm(chapters, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')):
        chapter_title = get_chapter_title(chapter)
        content = clean_text(chapter.get_content().decode('utf-8'))
        logging.info(f"Processing chapter {i+1}: {chapter_title}, content length: {len(content)}")
        
        try:
            stop_event = threading.Event()
            t = threading.Thread(target=loading_animation, args=(stop_event,))
            t.start()
            
            summary = summarize_text(content, api_key)
            total_tokens += len(content.split()) + len(summary.split())
            
            stop_event.set()
            t.join()
            
            summaries.append(f"## Chapter {i+1}: {chapter_title}\n\n{summary}\n")
            
            print(f"\n{colorama.Fore.GREEN}Chapter {i+1}: {chapter_title} - Summary:{colorama.Fore.RESET}")
            print(summary)
            print("\nProcessing next chapter...\n")
        except KeyboardInterrupt:
            print(f"\n{colorama.Fore.YELLOW}Process interrupted by user. Saving progress...{colorama.Fore.RESET}")
            break
        except Exception as e:
            logging.error(f"Error processing chapter {i+1}: {str(e)}")
            summaries.append(f"## Chapter {i+1}: {chapter_title}\n\nError processing this chapter: {str(e)}\n")
    
    return summaries, total_tokens

def create_book_summary(summaries, api_key):
    combined_summary = "\n".join(summaries)
    book_summary = summarize_text(combined_summary, api_key)
    return "# Book Summary\n\n" + book_summary + "\n\n# Chapter Summaries\n\n"

def save_summary(book_summary, summaries, epub_path, total_tokens):
    base_name = os.path.splitext(os.path.basename(epub_path))[0]
    output_dir = "summarized"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}_summary.md")
    
    estimated_cost = (total_tokens / 1000) * 0.06  # $0.06 per 1K tokens for GPT-4
    
    with open(output_path, 'w') as f:
        f.write(f"Estimated cost: ${estimated_cost:.2f}\n\n")
        f.write(book_summary)
        for summary in summaries:
            f.write(summary)
    
    print(f"\n{colorama.Fore.GREEN}Summary saved to:{colorama.Fore.RESET} {output_path}")
    print(f"{colorama.Fore.YELLOW}Estimated cost: ${estimated_cost:.2f}{colorama.Fore.RESET}")

def main():
    epub_path = "input.epub"
    
    try:
        with open('openai_key.txt', 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print(f"{colorama.Fore.RED}Error: openai_key.txt not found. Please create this file with your OpenAI API key.{colorama.Fore.RESET}")
        sys.exit(1)
    
    try:
        summaries, total_tokens = process_epub(epub_path, api_key)
        book_summary = create_book_summary(summaries, api_key)
        save_summary(book_summary, summaries, epub_path, total_tokens)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"{colorama.Fore.RED}An error occurred. Please check the logs for more information.{colorama.Fore.RESET}")

if __name__ == "__main__":
    main()
