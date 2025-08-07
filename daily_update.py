import base64
import json
import time
from dotenv import load_dotenv
import pytz
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import os
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import Select
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
from PIL import Image
from datetime import datetime
import random
import airtable
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

def setup_driver():
    """Setup Chrome driver for Heroku"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Chrome driver setup for Heroku with multiple path options
    if os.environ.get('DYNO'):
        # Chrome for Testing buildpack paths
        possible_chrome_paths = [
            '/app/.chrome-for-testing/chrome-linux64/chrome',
            '/app/.chrome-for-testing/chrome-linux64/google-chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/app/.apt/usr/bin/google-chrome',
            '/app/.apt/usr/bin/google-chrome-stable'
        ]
        
        possible_chromedriver_paths = [
            '/app/.chrome-for-testing/chromedriver-linux64/chromedriver',
            '/usr/bin/chromedriver',
            '/app/.apt/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver'
        ]
        
        # Find Chrome binary
        chrome_binary = None
        for path in possible_chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                break
        
        # Find ChromeDriver
        chromedriver_path = None
        for path in possible_chromedriver_paths:
            if os.path.exists(path):
                chromedriver_path = path
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            logger.info(f"Using Chrome binary: {chrome_binary}")
        if chromedriver_path:
            service = ChromeService(executable_path=chromedriver_path)
            logger.info(f"Using ChromeDriver: {chromedriver_path}")
        else:
            # Fallback to webdriver_manager if no chromedriver found
            chrome_install = ChromeDriverManager().install()
            service = ChromeService(executable_path=chrome_install)
    else:
        # Local development
        chrome_install = ChromeDriverManager().install()
        service = ChromeService(executable_path=chrome_install)
    
    return webdriver.Chrome(service=service, options=chrome_options)

def get_product_updates(driver, product_url):
    """Get updated product data for existing products"""
    try:
        driver.get(product_url)
        time.sleep(5)
        
        # Handle cookie dialog
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[text()='Close Dialog']")
            for button in cookie_buttons:
                try:
                    button.click()
                    time.sleep(1)
                except:
                    continue
        except:
            pass
        
        # Get product data
        product_data = get_updated_product_data(driver)
        sku_data = get_updated_sku_data(driver)
        
        return product_data, sku_data
        
    except Exception as e:
        logger.error(f"Error getting updates for {product_url}: {e}")
        return None, None

def get_updated_product_data(driver):
    """Get updated product fields"""
    try:
        # Coming Soon
        product_coming_soon = False
        
        # New Release
        try:
            new_release_elem = driver.find_element(By.XPATH, "//div[@class='ProductInformation_content-wrapper__ve36t']//span[.='new']")
            new_release = True if new_release_elem else False
        except:
            new_release = False
        
        # Excluded from Discounts
        exclude_from_discount = False
        
        # Price for Sorting
        try:
            price_for_sorting = driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
            price_for_sorting = int(price_for_sorting.split("$")[1].strip())
        except:
            price_for_sorting = 0
        
        # Percent Discount
        try:
            percent_discount = driver.find_element(By.XPATH, "//div[contains(@class,'PriceDisplay_alternative-sale-text__9WawT')]").text.strip()
            percent_discount = percent_discount.split(" ")[0]
            percent_discount = percent_discount.split("$")[1].strip()
            percent_discount = float(percent_discount)
            price_of_product = driver.find_element(By.XPATH, "(//span[@class='bfx-list-price'])[2]").text.strip()
            price_of_product = int(price_of_product.split("$")[1].strip())
            percent_discount = (percent_discount / price_of_product) * 100
            percent_discount = round(percent_discount, 2)
            percent_discount = f"{percent_discount}%"
        except:
            percent_discount = "0%"
        
        # Bonus/Filter 1-30 (sizes)
        bonus_filters = {}
        try:
            sizes_available = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
            sizes_list = [size.text.strip() for size in sizes_available]
            
            for idx, size in enumerate(sizes_list[:30]):
                bonus_filters[f"Bonus/Filter {idx + 1}"] = size
            
            # Check for 4E in product name
            try:
                h1_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'VariantDetailsEnhancedBuyPanel_productNameWording__')]")
                product_name = h1_element.text.strip().split('\n')[0].strip()
                if "(4E)" in product_name:
                    bonus_filters[f"Bonus/Filter {len(sizes_list) + 1}"] = "4E"
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Error getting bonus filters: {e}")
        
        # Scraper Update timestamp
        scrape_update = datetime.now(pytz.timezone('America/Los_Angeles')).strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "Coming Soon": product_coming_soon,
            "New Release": new_release,
            "Excluded from Discounts": exclude_from_discount,
            "Price for Sorting": price_for_sorting,
            "Percent Discount": percent_discount,
            "Scraper Update": scrape_update,
            **bonus_filters
        }
        
    except Exception as e:
        logger.error(f"Error getting updated product data: {e}")
        return {}

def get_updated_sku_data(driver):
    """Get updated SKU fields"""
    try:
        # MSRP
        try:
            list_price = driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
            msrp = list_price.replace("$", "")
        except:
            msrp = ""
        
        # Actual Price
        try:
            sale_price = driver.find_element(By.XPATH, "(//span[@data-testid='price-display-sales-price'])[2]").text.strip()
            actual_price = int(float(sale_price.replace("$", "")))
        except:
            try:
                actual_price = int(float(msrp))
            except:
                actual_price = 0
        
        # Sizes
        try:
            all_sizes_elements = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch']//span[contains(@id, 'size-label')]")
            available_sizes_elements = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
            
            all_sizes = [el.text.strip() for el in all_sizes_elements]
            available_sizes = [el.text.strip() for el in available_sizes_elements]
            
            sizes_dict = {size: 1 if size in available_sizes else 0 for size in all_sizes}
            sizes_text = json.dumps(sizes_dict)
        except:
            sizes_text = ""
        
        return {
            "Actual Price": actual_price,
            "Sizes": sizes_text
        }
        
    except Exception as e:
        logger.error(f"Error getting updated SKU data: {e}")
        return {}

def update_product_in_airtable(product_record_id, product_data):
    """Update product record in Airtable"""
    try:
        at.update("Products", product_record_id, product_data)
        logger.info(f"Updated product {product_record_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating product {product_record_id}: {e}")
        return False

def update_sku_in_airtable(sku_record_id, sku_data):
    """Update SKU record in Airtable"""
    try:
        at.update("SKUs", sku_record_id, sku_data)
        logger.info(f"Updated SKU {sku_record_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating SKU {sku_record_id}: {e}")
        return False

def get_existing_products():
    """Get ALL existing products from Airtable"""
    try:
        all_products = []
        offset = None
        
        while True:
            if offset:
                products = at.get("Products", offset=offset)
            else:
                products = at.get("Products")
            
            all_products.extend(products["records"])
            
            # Check if there are more records
            if "offset" in products:
                offset = products["offset"]
            else:
                break
        
        logger.info(f"Retrieved {len(all_products)} products from Airtable")
        return all_products
        
    except Exception as e:
        logger.error(f"Error getting existing products: {e}")
        return []

def find_product_by_url(products, url):
    """Find product record by source URL with flexible matching"""
    # Normalize the search URL
    search_url = url.rstrip('/')
    
    for product in products:
        product_url = product.get("fields", {}).get("Source URL", "")
        if product_url:
            # Normalize the product URL
            normalized_product_url = product_url.rstrip('/')
            
            # Try exact match first
            if normalized_product_url == search_url:
                return product
            
            # Try matching by product ID (last part of URL)
            try:
                search_id = search_url.split('/')[-1].split('.')[0]
                product_id = normalized_product_url.split('/')[-1].split('.')[0]
                if search_id == product_id:
                    return product
            except:
                pass
    
    return None

def main():
    """Main function to run daily updates"""
    logger.info("Starting daily product updates")
    
    # Load scraped product links
    if not os.path.exists("scraped_product_links.txt"):
        logger.error("scraped_product_links.txt not found")
        return
    
    with open("scraped_product_links.txt", "r") as file:
        product_urls = [line.strip() for line in file.readlines() if line.strip()]
    
    if not product_urls:
        logger.info("No product URLs to update")
        return
    
    # Get existing products from Airtable
    existing_products = get_existing_products()
    
    # Setup driver
    driver = setup_driver()
    
    try:
        for url in product_urls:
            logger.info(f"Processing: {url}")
            
            # Find existing product record
            product_record = find_product_by_url(existing_products, url)
            if not product_record:
                logger.warning(f"No existing product found for URL: {url}")
                continue
            
            # Get updated data
            product_data, sku_data = get_product_updates(driver, url)
            
            if product_data:
                # Update product
                update_product_in_airtable(product_record["id"], product_data)
            
            if sku_data:
                # Find and update associated SKUs
                try:
                    sku_ids = product_record.get("fields", {}).get("SKUs", [])
                    for sku_id in sku_ids:
                        update_sku_in_airtable(sku_id, sku_data)
                except Exception as e:
                    logger.error(f"Error updating SKUs for product {product_record['id']}: {e}")
            
            # Sleep between requests to be respectful
            time.sleep(2)
    
    finally:
        driver.quit()
    
    logger.info("Daily product updates completed")

if __name__ == "__main__":
    main() 