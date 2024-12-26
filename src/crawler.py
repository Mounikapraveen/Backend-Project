import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# List of e-commerce domains to crawl (example)
DOMAINS = [
    "http://example1.com", "http://example2.com", "http://example3.com"
]

# Regex patterns for product URLs
PRODUCT_PATTERNS = [
    r"/product/\d+",   # Matches /product/12345
    r"/item/\d+",      # Matches /item/56789
    r"/p/\d+"          # Matches /p/98765
]

async def fetch_html(url: str, session: aiohttp.ClientSession):
    """Fetch HTML content of a given URL asynchronously."""
    async with session.get(url) as response:
        return await response.text()

async def extract_product_urls(html: str):
    """Extract product URLs from the HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()

    # Look for <a> tags with href attributes
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        if any(re.search(pattern, href) for pattern in PRODUCT_PATTERNS):
            links.add(href)

    return links

def fetch_dynamic_content(url: str):
    """Use Selenium to fetch JavaScript-heavy content."""
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    # Wait for JavaScript to load
    driver.implicitly_wait(5)  # Adjust the wait time based on the website's load time

    html = driver.page_source
    driver.quit()
    return html

async def crawl_domain(domain: str, session: aiohttp.ClientSession):
    """Crawl a single domain to extract product URLs."""
    print(f"Crawling domain: {domain}")
    
    # Fetch static content first
    html = await fetch_html(domain, session)
    product_urls = await extract_product_urls(html)

    # If no product URLs are found, try dynamic content with Selenium
    if not product_urls:
        print(f"No product URLs found on {domain}. Trying dynamic content...")
        html = fetch_dynamic_content(domain)
        product_urls = await extract_product_urls(html)

    return domain, list(product_urls)

async def crawl_all_domains():
    """Crawl all domains concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [crawl_domain(domain, session) for domain in DOMAINS]
        results = await asyncio.gather(*tasks)
    
    # Store the results in a JSON file
    all_product_urls = {domain: urls for domain, urls in results}
    with open('product_urls.json', 'w') as f:
        json.dump(all_product_urls, f, indent=4)

if __name__ == "__main__":
    asyncio.run(crawl_all_domains())
