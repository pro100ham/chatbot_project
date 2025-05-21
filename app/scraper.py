import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

START_URLS = [
    "https://wiki.ucu.edu.ua/start",
    "https://ucu.edu.ua/index",
    "https://vstup.ucu.edu.ua/start"
]

MAX_DEPTH = 40
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_domain(url):
    return urlparse(url).netloc

def scrape_site(start_url):
    visited = set()
    text_data = []
    domain = get_domain(start_url)

    def scrape_page(url, depth):
        if depth > MAX_DEPTH or url in visited:
            return

        visited.add(url)
        print(f"🔎 Scraping: {url} (depth={depth})")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                print(f"🚫 Skipping (non-HTML or blocked): {url}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            main = soup.find("main") or soup.body
            title = soup.title.string.strip() if soup.title else ""
            header = main.find("h1").get_text(strip=True) if main and main.find("h1") else ""

            if main:
                texts = main.stripped_strings
                combined = f"{title}\n{header}\n" + " ".join(texts)
                if len(combined) > 100 and combined not in text_data:
                    text_data.append(combined)

            for a in soup.find_all("a", href=True):
                link = urljoin(start_url, a["href"].split("#")[0])

                if (
                    get_domain(link) == get_domain(start_url)
                    and link not in visited
                    and "?do=" not in link
                    and "/en:" not in link
                    and not any(x in link for x in ["#top", "#nav", "/feed"])
                ):
                    scrape_page(link, depth + 1)

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")

    # 🔁 Запускаємо рекурсію
    scrape_page(start_url, 0)

    return domain, text_data

# 🔁 Обходимо всі сайти
all_blocks = []
for url in START_URLS:
    domain, chunks = scrape_site(url)
    for i, block in enumerate(chunks, 1):
        all_blocks.append(f"[Сайт: {domain}] [Розділ {i}]\n{block.strip()}\n\n")

# 💾 Запис
with open("university_texts.txt", "w", encoding="utf-8") as f:
    f.writelines(all_blocks)

print(f"✅ Готово. Загальна кількість блоків: {len(all_blocks)}")
