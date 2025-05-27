from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import csv

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def parse_listing(card_div):
    """Extract data from a single listing element (WebElement)"""
    try:
        link = card_div.find_element(By.CSS_SELECTOR, 'a.js__product-link-for-product-id')
        product_id = link.get_attribute('data-product-id')
        href = link.get_attribute('href')
        title = link.get_attribute('title').strip()
    except NoSuchElementException:
        return None

    images = []
    for img in card_div.find_elements(By.CSS_SELECTOR, 'img[data-img]'):
        src = img.get_attribute('data-img') or img.get_attribute('src')
        if src:
            images.append(src)

    price = area = toilet = location = description = published = ''
    try:
        price = card_div.find_element(By.CSS_SELECTOR, 'span.re__card-config-price').text.strip()
    except NoSuchElementException:
        pass
    try:
        area = card_div.find_element(By.CSS_SELECTOR, 'span.re__card-config-area').text.strip()
    except NoSuchElementException:
        pass
    try:
        toilet = card_div.find_element(By.CSS_SELECTOR, 'span.re__card-config-toilet span').text.strip()
    except NoSuchElementException:
        pass
    try:
        location = card_div.find_element(By.CSS_SELECTOR, 'div.re__card-location span:not(.re__card-config-dot)').text.strip()
    except NoSuchElementException:
        pass
    try:
        description = card_div.find_element(By.CSS_SELECTOR, 'div.re__card-description').text.strip()
    except NoSuchElementException:
        pass
    try:
        published = card_div.find_element(By.CSS_SELECTOR, 'span.re__card-published-info-published-at').text.strip()
    except NoSuchElementException:
        pass

    return {
        'product_id': product_id,
        'title': title,
        'url': href,
        'images': images,
        'price': price,
        'area': area,
        'toilet': toilet,
        'location': location,
        'description': description,
        'published': published
    }


def scrape_page(page_num):
    """Mở session mới, load page và parse listings"""
    driver = create_driver()
    url = f"https://batdongsan.com.vn/cho-thue-sang-nhuong-cua-hang-ki-ot-ha-noi/p{page_num}"
    print(f"Starting new session for page {page_num}: {url}")
    driver.get(url)
    time.sleep(3)

    cards = driver.find_elements(By.CSS_SELECTOR, 'div.js__card')
    print(f"  -> Found {len(cards)} listings on page {page_num}")
    listings = []
    for card in cards:
        data = parse_listing(card)
        if data:
            listings.append(data)

    driver.quit()
    return listings


def main(max_pages=None, delay=2):
    all_listings = []
    page = 1
    while True:
        print(f"== Processing page {page} ==")
        listings = scrape_page(page)
        if not listings:
            print("No listings found, stopping.")
            break
        all_listings.extend(listings)

        driver = create_driver()
        driver.get(f"https://batdongsan.com.vn/cho-thue-sang-nhuong-cua-hang-ki-ot-ha-noi/p{page}")
        time.sleep(2)
        try:
            driver.find_element(By.CSS_SELECTOR, 'a.re__pagination-icon[pid]')
            has_next = True
        except NoSuchElementException:
            has_next = False
        driver.quit()

        print(f"Next page exists: {has_next}")
        if not has_next or (max_pages and page >= max_pages):
            break
        page += 1
        time.sleep(delay)

    if all_listings:
        keys = all_listings[0].keys()
        with open('kiot_listings.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_listings)
        print(f"Saved {len(all_listings)} listings to CSV.")
    else:
        print("No data scraped.")

if __name__ == '__main__':
    main()
