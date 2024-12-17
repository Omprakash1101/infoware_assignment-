import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
import json

# User Configuration
AMAZON_LOGIN_URL = "https://www.amazon.in/ap/signin"
BEST_SELLER_URL = "https://www.amazon.in/gp/bestsellers/"
CATEGORIES = [
    "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
    "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
    "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
    "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
]
MAX_PRODUCTS = 1500
DISCOUNT_THRESHOLD = 50
USERNAME = "omprakashgopi2k05@gmail.com"
PASSWORD = "Jayom2005@opm11"
COOKIES_FILE = "cookies.json"

def init_driver():
    """Initialize the Selenium WebDriver"""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS sandboxing
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource issues
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--remote-debugging-port=9222")  # Enable debugging port
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

def load_cookies(driver, cookies_file):
    """Load cookies from a JSON file into the browser."""
    driver.get("https://www.amazon.in/")
    with open(cookies_file, "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            if "sameSite" in cookie:
                del cookie["sameSite"]  # Remove unsupported keys
            driver.add_cookie(cookie)
    driver.refresh()
    print("[INFO] Cookies loaded. Login skipped.")

def amazon_login(driver, username, password):
    """Automates Amazon Login Process"""
    driver.get(AMAZON_LOGIN_URL)
    try:
        # Enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_field.send_keys(username)
        email_field.send_keys(Keys.RETURN)
        
        # Enter password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        
        # Wait after login
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "nav-belt")))
        print("[INFO] Login successful.")
    except TimeoutException:
        print("[ERROR] Login failed. Check credentials or 2FA requirements.")
        driver.quit()
        exit()

def extract_discount(price, discounted_price):
    """Calculates the discount percentage."""
    try:
        price = float(price.replace(",", ""))
        discounted_price = float(discounted_price.replace(",", ""))
        discount = 100 * (price - discounted_price) / price
        return round(discount, 2)
    except:
        return 0

def scrape_category(driver, category_url, category_name):
    """Scrapes product details from a category URL."""
    driver.get(category_url)
    products = []
    count = 0

    while count < MAX_PRODUCTS:
        try:
            # Find all products on the current page
            items = driver.find_elements(By.CSS_SELECTOR, "div.zg-item-immersion")
            for item in items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "div.p13n-sc-truncate").text.strip()
                    price_element = item.find_element(By.CSS_SELECTOR, "span.p13n-sc-price")
                    price = price_element.text.replace("\u20b9", "").strip()
                    
                    # Placeholder: Discount calculation; simulate a fake discount logic
                    discount = extract_discount(str(float(price) * 1.5), price)
                    
                    if discount > DISCOUNT_THRESHOLD:  # Focus only products >50% discount
                        product_data = {
                            "Category": category_name,
                            "Name": name,
                            "Price (INR)": price,
                            "Discount (%)": discount,
                            "Rating": "Not Available",  # Add logic to scrape rating
                            "Sold By": "Not Available",
                        }
                        products.append(product_data)
                        count += 1

                except NoSuchElementException:
                    pass  # Ignore items with missing details

            # Click 'Next' button to paginate
            next_button = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
        except NoSuchElementException:
            print("[INFO] End of page reached for category.")
            break
    return products

def save_to_csv(data, filename="amazon_products.csv"):
    """Save scraped data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"[INFO] Data saved to {filename}")

def main():
    driver = init_driver()
    try:
        # Step 1: Attempt to load cookies and skip login
        try:
            load_cookies(driver, COOKIES_FILE)
        except Exception as e:
            print(f"[WARN] Failed to load cookies: {e}. Proceeding with login.")
            amazon_login(driver, USERNAME, PASSWORD)
        
        # Step 2: Scrape categories
        all_products = []
        for url in CATEGORIES[:10]:
            category_name = url.split("/")[-1]  # Extract category name from URL
            print(f"[INFO] Scraping category: {category_name}")
            category_products = scrape_category(driver, url, category_name)
            all_products.extend(category_products)

        # Step 3: Save data to CSV
        save_to_csv(all_products)
    finally:
        driver.quit()
        print("[INFO] Scraping completed.")

if __name__ == "__main__":
    main()
