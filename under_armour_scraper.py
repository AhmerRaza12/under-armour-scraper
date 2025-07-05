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


load_dotenv()

AIRTABLE_BASE_ID= os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY= os.getenv("AIRTABLE_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

# Initialize data lists
Products_tab_data = []
SKUS_tab_data = []
Imported_reviews_tab_data = []

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument('--disable-blink-features=AutomationControlled')
# chrome_options.add_argument('--headless=new')
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
# chrome_options.add_argument(f'--proxy-server={proxy_ip}')
# chrome_options.add_argument('--window-size=1920,1080')
# chrome_options.add_argument("--headless=new")
chrome_install = ChromeDriverManager().install()
folder = os.path.dirname(chrome_install)
chromedriver_path = os.path.join(folder, "chromedriver.exe")
service = ChromeService(executable_path=chromedriver_path, log_path='NUL')



driver = webdriver.Chrome(service=service, options=chrome_options)




def upload_image_to_imgbb(image_path):
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": image_base64
    }
    response = requests.post(url, data=payload)
    return response.json()["data"]["url"]


def get_links():
    links = []
    try:
        driver.get("https://www.underarmour.com/en-us/c/shoes/mens%2Bwomens%2Badult_unisex-sneakers%2Bboots/?srule=top-sellers")
        time.sleep(5)
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[text()='Close Dialog']")
            for button in cookie_buttons:
                try:
                    button.click()
                    time.sleep(1)
                except (StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException):
                    continue
        except:
            pass

        while True:
            time.sleep(5)
            product_links = driver.find_elements(By.XPATH, "//div[contains(@class, 'ProductGrid_product-listing')]//a[contains(@class, 'ProductTile_product-image-link')]")
            for link in product_links:
                try:
                    href = link.get_attribute("href")
                    if href and href not in links:
                        links.append(href)
                except Exception as e:
                    print("Error getting link:", e)
                    continue
            try:
                next_button = driver.find_element(By.XPATH, "//a[.='Next']")
                if next_button.is_enabled():
                    driver.execute_script("arguments[0].click();", next_button)
                else:
                    break
            except NoSuchElementException:
                break  
            except Exception as e:
                print("Error clicking next:", e)
                break
            

    except Exception as e:
        print("Error loading page:", e)
        return []

    return links
 
def scrape_data(links):
    # scrape last link
    for link in links[23:24]:
        driver.get(link)
        time.sleep(5)

        try:
            # Extract and upload SKUs first
            skus_data = get_SKUS_data(driver)
            sku_record_ids = []
            if skus_data:
                for sku in skus_data:
                    created_sku = at.create("SKUs", sku)
                    sku_record_id = created_sku["id"]
                    sku_record_ids.append(sku_record_id)
                    print(f"[✔] Created SKU: {sku.get('Name')} → ID: {sku_record_id}")
            else:
                print("[⚠] No SKUs data found")

            # Extract and upload Product data with SKU references
            product_data = get_product_data(driver, sku_record_ids)
            created_product = at.create("Products", product_data)
            product_record_id = created_product["id"]
            print(f"[✔] Created Product: {product_data.get('Name')} → ID: {product_record_id}")

            # Extract and upload Reviews with linked Product ID
            imported_reviews_data = get_imported_reviews(driver, product_record_id)
            for review in imported_reviews_data:
                at.create("Imported Reviews", review)

        except Exception as e:
            print(f"[✘] Error processing {link}: {e}")
            continue


def get_product_data(driver, sku_record_ids):
    time.sleep(2)
    
    try:
        dialog_button = driver.find_element(By.XPATH, "(//button[contains(@class,'Dialog_close-button__LzXL1')])[5]")
        dialog_button.click()
        time.sleep(1)
    except (StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException, NoSuchElementException):
        pass  # If the button is not interactable, we can skip it
    try:
        h1_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'VariantDetailsEnhancedBuyPanel_productNameWording__')]")
        full_text = h1_element.text.strip()
        product_name = full_text.split('\n')[0].strip()  # Get only the first line
        color_name = driver.find_element(By.XPATH, "//legend//span[@aria-hidden='true']").text.strip()
        # split color name by - and get the first part and color id in the 1 index
        color_name_split = color_name.split(" - ")
        color_name = color_name_split[0]
        color_id = color_name_split[1]
        sku = driver.current_url.split("/")[-1].split(".")[0] + "-" + color_id
        name_of_product = f"{product_name} {sku}"
        name_of_product = name_of_product.replace("UA", "Under Armour",1)
    
    except:
        name_of_product =""
        color_name =""
    try:
        breadcrumb_elements = driver.find_elements(By.XPATH, "//nav[@aria-label='Breadcrumb']//a")
        breadcrumb_texts = [el.text.strip() for el in breadcrumb_elements]
    except:
        breadcrumb_texts = []
    category_keywords = {
     r"\bwomen\b":  "Women's Shoes",
    r"\bmen\b":    "Men's Shoes",
    r"\bunisex\b": "Unisex Shoes",
    }
    matched_categories = set()
    for text in breadcrumb_texts:
        lowered = text.lower()
        for keyword, category in category_keywords.items():
            if re.search(keyword, lowered):
                matched_categories.add(category)
    filter_category_ids = []
    for category in matched_categories:
        try:
        # Escape single quote for Airtable formula by using double quotes
            escaped_value = category.replace('"', '\"')
            formula = f'{{Name}} = "{escaped_value}"'
            print(f"[ℹ] Fetching category '{category}' with formula: {formula}")
            result = at.get("Services & Collections", filter_by_formula=formula)
            if result["records"]:
                filter_category_ids.append(result["records"][0]["id"])
        except Exception as e:
            print(f"[⚠] Error fetching category '{category}': {e}")
            continue
   

    try:
        product_source_url = driver.current_url
    except:
        product_source_url = ""
    product_coming_soon = False
    exclude_from_discount = False
    try:
        new_release = driver.find_element(By.XPATH, "//div[@class='ProductInformation_content-wrapper__ve36t']//span[.='new']")
        if new_release:
            new_release = True
    except:
        new_release = False
    # sku can be found in the URL https://www.underarmour.com/en-us/p/sportswear/ua_phantom_4_mens_shoes/3027593.html?dwvar_3027593_color=925 here 3027593 is the sku

    try:
        try:
            # it doesnt exists till we scrall down a bit
            driver.execute_script("window.scrollBy(0, 700);")
            time.sleep(4)
            # try the xpath //div[contains(@class,'AnimationWrapper_animate-section__PujEV AnimationWrapper_fade__LEwLx AnimationWrapper_from-left__NKLLZ AnimationWrapper_is-visible__XfavV')]
            description1 = driver.find_element(By.XPATH, "//div[contains(@class,'AnimationWrapper_animate-section__PujEV AnimationWrapper_fade__LEwLx AnimationWrapper_from-left__NKLLZ AnimationWrapper_is-visible__XfavV')]").text.strip()

            print("Description 1 is not empty", description1)
        except:
            print("Description 1 is empty")
            description1 = ""
        product_details_accordion_expand_button = driver.find_element(By.XPATH, "(//div[@class='Accordion_accordion--heading__Qzk_d ua-accordion-heading '])[2]")
        driver.execute_script("arguments[0].scrollIntoView(true);", product_details_accordion_expand_button)
        time.sleep(1)
        driver.execute_script("window.scrollBy(0, -100);")
        time.sleep(1)
        driver.execute_script("arguments[0].click();", product_details_accordion_expand_button)
        time.sleep(1)
        description2 = driver.find_element(By.XPATH, "//div[@data-testid='accordion-detail'][contains(., 'Product Details')]").text.strip()
        description = f"{description1}\n{description2}"

    except:
        description = ""
    try:
        description1_html = f"<p>{description1}</p>" if description1 else ""

    # Get HTML of accordion content
        heading_elem = driver.find_element(By.XPATH, "//div[@data-testid='accordion-detail']//div[contains(text(), 'Product Details')]")
        heading_html = f"<div>{heading_elem.text.strip()}</div>"
        details_elem = driver.find_element(By.XPATH, "(//div[@data-testid='accordion-content']//ul)[1]")
        details_html = details_elem.get_attribute("outerHTML").strip()
        description2_element = driver.find_element(By.XPATH, "//div[@data-testid='accordion-detail'][contains(., 'Product Details')]")
        description2_html = f"{heading_html}\n{details_html}"

    # Combine
        product_description = f"{description1_html}{description2_html}"

    except :
        product_description = ""
    try:
        # model name can be found in product_name without the first word that is UA 
        model_name = product_name.split(" ", 1)[-1] if " " in product_name else product_name
    except:
        model_name = ""
    try:
        price_for_sorting=driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
        # price for sorting is like $120 we need just 120 and in number
        price_for_sorting = price_for_sorting.split("$")[1].strip()
        price_for_sorting = int(price_for_sorting)
    except :
        price_for_sorting = 0
    try:
        size_and_fit_expand_button = driver.find_element(By.XPATH, "(//div[@class='Accordion_accordion--heading__Qzk_d ua-accordion-heading '])[3]")
        # a little above scroll to the size and fit expand button
        driver.execute_script("arguments[0].scrollIntoView(true);", size_and_fit_expand_button)
        time.sleep(1)
        # scroll a little above the size and fit expand button
        driver.execute_script("window.scrollBy(0, -100);")
        time.sleep(1)
        driver.execute_script("arguments[0].click();", size_and_fit_expand_button)
        time.sleep(1)
        fit=driver.find_element(By.XPATH,"//ul[@class='SizeAndFit_fit-specs__LLcEm']").text.strip()
    except:
        fit = ""
    try:
        percent_discount = driver.find_element(By.XPATH, "//div[contains(@class,'PriceDisplay_alternative-sale-text__9WawT')]").text.strip()
        # it comes as $35 off so we need to get the number and calculate the percentage
        percent_discount = percent_discount.split(" ")[0]
        percent_discount = percent_discount.split("$")[1].strip()
        percent_discount = float(percent_discount)
        # get the price of the product
        price_of_product = driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
        price_of_product = price_of_product.split("$")[1].strip()
        price_of_product = int(price_of_product)
        # calculate the percentage
        percent_discount = (percent_discount / price_of_product) * 100
        percent_discount = round(percent_discount, 2)
        percent_discount = f"{percent_discount}%"
    except:
        percent_discount ="0%"
    try:
        # get brand from airtable table Filters by Name column value "Under Armour" and get that record id
        brand_record_id = at.get("Filters", filter_by_formula="Name = 'Under Armour'")
        # print(brand_record_id["records"][0]["id"])
        brand_record_id = brand_record_id["records"][0]["id"]
    except:
        brand_record_id = ""
    try:
        # first we have to create a record in Filters table with Name column value "model_name" and get that record id
        created_model_name = at.create("Filters", {"Name": model_name})
        model_name_record_id = created_model_name["id"]
    except:
        model_name_record_id = ""
    
    
    # Select size chart image based on gender
    try:
        if any('women' in cat.lower() for cat in matched_categories):
            image_filename = "women_combined_size_chart.png"
        else:
            image_filename = "combined_size_chart.png"
        # image is in current directory
        image_path = os.path.join(os.getcwd(), image_filename)
        try:
            size_chart_image_url = upload_image_to_imgbb(image_path)
        except Exception as e:
            print(f"Error uploading size chart image: {e}")
            size_chart_image_url = ""
    except:
        size_chart_image_url = ""
   
    #  Pacific Time
    scrape_update = datetime.now(pytz.timezone('America/Los_Angeles')).strftime("%Y-%m-%d %H:%M:%S")

    data={
        "Name": name_of_product,
        "Source URL": product_source_url,
        "Coming Soon": product_coming_soon,
        "New Release": new_release,
        "Excluded from Discounts": exclude_from_discount,
        "SKU/Product ID": sku,
        "Description": description,
        "Product Description": product_description,
        "SEO Title Tag": "Under Armour " + model_name,
        "Product Brand or Title": "Under Armour",
        # "Model Name": model_name,
         "Size Guide": [{
            "url": size_chart_image_url,
        }],
        "Model Name":[model_name_record_id],
        "Color Name": color_name,
        "Price for Sorting": price_for_sorting,
        # "Fit": fit,
        "Percent Discount": percent_discount,
        
        "Scraper Update": scrape_update,
        "Brand":[brand_record_id]


    }
    
    # Add SKU references
    if sku_record_ids:
        data["SKUs"] = sku_record_ids
    if filter_category_ids:
        data["Filter Category/ies"] = filter_category_ids
    try:
        sizes_available = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
        sizes_list = [size.text.strip() for size in sizes_available]

        for idx, size in enumerate(sizes_list[:30]):
            data[f"Bonus/Filter {idx + 1}"] = size
        bonus_filter_idx = len(sizes_list)
    except Exception as e:
        print(f"[⚠] Error generating bonus filters: {e}")
        bonus_filter_idx = 0

    # If (4E) is in the product name, add '4E' to a Bonus/Filter
    if "(4E)" in name_of_product:
        data[f"Bonus/Filter {bonus_filter_idx + 1}"] = "4E"
    
    return data
    

def get_SKUS_data(driver):
    time.sleep(2)
    try:
        h1_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'VariantDetailsEnhancedBuyPanel_productNameWording__')]")
        full_text = h1_element.text.strip()
        product_name = full_text.split('\n')[0].strip()  # Get only the first line
        color_name = driver.find_element(By.XPATH, "//legend//span[@aria-hidden='true']").text.strip()
        # split color name by - and get the first part and color id in the 1 index
        color_name_split = color_name.split(" - ")
        color_name = color_name_split[0]
        color_id = color_name_split[1]
        sku = driver.current_url.split("/")[-1].split(".")[0] + "-" + color_id
        name_of_product = f"{product_name} {sku}"
        name_of_product = name_of_product.replace("UA", "Under Armour",1)
    
    except:
        name_of_product = ""
    try:
        main_image_url = driver.find_element(By.XPATH, "(//div[@class='ProductImages_pdpImages__wK1mQ']//img)[1]").get_attribute("src")
        if not main_image_url:
            main_image_url = ""
    except:
        main_image_url = ""
    try:
        # get except the first image
        more_images_url = driver.find_elements(By.XPATH, "//div[@class='ProductImages_pdpImages__wK1mQ']//img")[1:]
        more_images_url = [image.get_attribute("src") for image in more_images_url if image.get_attribute("src")]
    except:
        more_images_url = []
    invalid_main_image = (
    not main_image_url or
    main_image_url.startswith("data:image/gif") or
    main_image_url.strip() == ""
    )
    # If main_image_url is empty, use the first image from more_images_url
    if invalid_main_image and more_images_url:
        main_image_url = more_images_url[0]
        more_images_url = more_images_url[1:]  # Remove the first image from more_images since it's now the main image
        print(f"[ℹ] Replaced invalid main image with first more image: {main_image_url}")
    elif invalid_main_image:
        print("[⚠] Main image is invalid and no more images found")
    else:
        print(f"[ℹ] Using original main image: {main_image_url}")
    
    try:
        list_price = driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
        price_text = list_price.replace("$", "")
        
    except :
        price_text = ""
    try:
        sale_price = driver.find_element(By.XPATH, "(//span[@data-testid='price-display-sales-price'])[2]").text.strip()
        price_number = int(float(sale_price.replace("$", "")))
    except:
    # If no discounted price, fallback to list price
        try:
            price_number = int(float(price_text))
        except:
            price_number = 0

    try:
        all_sizes_elements = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch']//span[contains(@id, 'size-label')]")
        available_sizes_elements = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
    
        all_sizes = [el.text.strip() for el in all_sizes_elements]
        available_sizes = [el.text.strip() for el in available_sizes_elements]
    
        sizes_dict = {size: 1 if size in available_sizes else 0 for size in all_sizes}
        sizes_text = json.dumps(sizes_dict)
    except:
        sizes_text = ""
    


    
        
    data={
        "Name": name_of_product,
        "Price (Text)": price_text,
        "Price (Number)": price_number,
        "Price (Currency)": 0,
        "Sizes": sizes_text,
        "SKU Values (Text)": sku,
        "SKU/Product ID": sku

    }
    
    # Only add Main Image if there's a valid URL
    if main_image_url:
        data["Main Image"] = [{"url": main_image_url}]
    
    # Only add More Images if there are additional images
    if more_images_url:
        data["More Images"] = [{"url": url} for url in more_images_url]
    
    return [data]

def get_imported_reviews(driver, product_record_id):
    try:
        time.sleep(2)
        dialog_button = driver.find_element(By.XPATH, "(//button[contains(@class,'Dialog_close-button__LzXL1')])[5]")
        dialog_button.click()
        time.sleep(1)
    except (StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException, NoSuchElementException):
        pass 
    
    # Use the passed product_record_id instead of trying to find it
    if not product_record_id:
        print("No product record ID provided, skipping reviews")
        return []
        
    try:
        reviews_accordion_expand_button = driver.find_element(By.XPATH, "(//div[@class='Accordion_accordion--heading__Qzk_d ua-accordion-heading '])[5]")
        driver.execute_script("arguments[0].scrollIntoView(true);", reviews_accordion_expand_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", reviews_accordion_expand_button)
        time.sleep(1)
        all_reviews_button = driver.find_element(By.XPATH, "//button[contains(.,'See All Reviews')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", all_reviews_button)
        # scroll a little above the all reviews button
        driver.execute_script("window.scrollBy(0, -200);")

        time.sleep(1)
        all_reviews_button.click()
        time.sleep(1)
        while True:
            try:
                show_more_button = driver.find_element(By.XPATH, "//button[contains(text(),'Show More')]")
                if show_more_button:
                    print("show more button found")
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
                    time.sleep(2)
                    show_more_button.click()
                    time.sleep(1)
                else:
                    print("all reviews loaded")
                    break
            except:
                print("no show more button found")
                break
        person_names = driver.find_elements(By.XPATH, "//div[@class='Reviews_reviews__6YQse Reviews_full__r5YAF']//div[@class='ReviewCard_review-card__XhxXV']//div[@class='ReviewCard_frame__xdRaA']//div[contains(@class,'ReviewCard_div__frJBZ')][1]")
        date_revieweds = driver.find_elements(By.XPATH, "//div[@class='Reviews_reviews__6YQse Reviews_full__r5YAF']//div[@class='ReviewCard_review-card__XhxXV']//div[@class='ReviewCard_frame__xdRaA']//div[contains(@class,'ReviewCard_div__frJBZ')][2]")
        review_titles = driver.find_elements(By.XPATH, "//div[@class='Reviews_reviews__6YQse Reviews_full__r5YAF']//div[@class='ReviewCard_text-wrapper__EWy86']")
        review_comments = driver.find_elements(By.XPATH, "//div[@class='Reviews_reviews__6YQse Reviews_full__r5YAF']//div[@class='ReviewCard_review-card__XhxXV']//div[contains(@style,'--line-clamp: 3;')]//p")
        review_frames = driver.find_elements(By.XPATH, "//div[@class='Reviews_reviews__6YQse Reviews_full__r5YAF']//div[@class='ReviewCard_review-card__XhxXV']")
        
        reviews_data = []
        for review_person in review_frames:
            
            raw_name = person_names[review_frames.index(review_person)].text.strip()
            if not raw_name:
                raw_name = f"User{random.randint(10000, 99999)}"
            person_name_text = raw_name
            date_reviewed = date_revieweds[review_frames.index(review_person)].text.strip()
            review_title = review_titles[review_frames.index(review_person)].text.strip()
            review_comment = review_comments[review_frames.index(review_person)].text.strip()
                # we need to convert the date_reviewed to datetime object but it gets the date like "8 Days Ago", "2 Months Ago", "1 Year Ago" etc.
            if "days ago" in date_reviewed:
                days_ago = int(date_reviewed.split(" ")[0])
                date_reviewed = datetime.now() - pd.Timedelta(days=days_ago)
            elif "months ago" in date_reviewed:
                months_ago = int(date_reviewed.split(" ")[0])
                date_reviewed = datetime.now() - pd.Timedelta(days=months_ago * 30)
            elif "month ago" in date_reviewed:
                date_reviewed = datetime.now() - pd.Timedelta(days= 30)
            elif "years ago" in date_reviewed:
                years_ago = int(date_reviewed.split(" ")[0])
                date_reviewed = datetime.now() - pd.Timedelta(days=years_ago * 365)
            elif "year ago" in date_reviewed:
                date_reviewed = datetime.now() - pd.Timedelta(days= 365)
            else:
                date_reviewed = datetime.now()
            review_title = review_titles[review_frames.index(review_person)].text.strip()
            review_comment = review_comments[review_frames.index(review_person)].text.strip()
            try:
                rating = driver.execute_script("""
                    const review = arguments[0];
                    const stars = review.querySelectorAll("div.StarRatings_star-ratings__A55mj svg");
                    let count = 0;
                    stars.forEach(svg => {
                    if (svg.getAttribute("title") === "filled-star") count++;
                    });
                    return count;
                    """, review_person)
            except:
                rating = 0
            try:
                img_urls = review_person.find_elements(By.XPATH, ".//img")
                img_urls = [img.get_attribute("src") for img in img_urls]
            except:
                img_urls = []
                    
                    
            data ={
                "Name": person_name_text,
                "Product Reviewed": [product_record_id],
                "Date": date_reviewed.strftime('%Y-%m-%d'),
                "Review Title": review_title,
                "Review Comment": review_comment,
                "Rating": rating,
            }
            
            # Only add Review Image(s) if there are valid image URLs
            if img_urls:
                data["Review Image(s)"] = [{"url": img_url} for img_url in img_urls]
            
            reviews_data.append(data)
                
    except Exception as e:
        print(f"Error getting imported reviews: {e}")
        reviews_data = []
    
        
    return reviews_data
        


if __name__ == "__main__":
    # Load product links from file
    if os.path.exists("product_links.txt"):
        with open("product_links.txt", "r") as file:
            links = [line.strip() for line in file.readlines()]
    else:
        print("No product_links.txt file found.")
        links = []

    if links:
        scrape_data(links)
    else:
        print("No links to process.")

    driver.quit()
    
   
    
 
    
    
    
    

    