import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE_URL = "https://mon.gov.ua/"  
MAX_DEPTH = 8  # максимальна глибина переходів
visited_urls = set()
text_data = []

def scrape_page(url, depth=0):
    if depth > MAX_DEPTH:
        return 

    print(f"Scraping: {url} (depth={depth})")
    try:
        response = requests.get(url, timeout=10)
        if "text/html" not in response.headers.get("Content-Type", ""):
            return
        soup = BeautifulSoup(response.text, "html.parser")
        main = soup.find("main") or soup.body
        if main:
            texts = main.stripped_strings
            combined = " ".join(texts)
            text_data.append(combined)
        for a in soup.find_all("a", href=True):
            link = urljoin(BASE_URL, a["href"])
            if link.startswith(BASE_URL) and link not in visited_urls:
                visited_urls.add(link)
                time.sleep(1)
                scrape_page(link, depth=depth+1) 
    except Exception as e:
        print(f"Error scraping {url}: {e}")

# Стартуємо з базової глибини 0
visited_urls.add(BASE_URL)
scrape_page(BASE_URL, depth=0)

with open("university_texts.txt", "w", encoding="utf-8") as f:
    for block in text_data:
        f.write(block + "\n\n")