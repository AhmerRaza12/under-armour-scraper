import base64
import time
from dotenv import load_dotenv
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
import airtable


load_dotenv()

AIRTABLE_BASE_ID= os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY= os.getenv("AIRTABLE_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)






chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument(f'--proxy-server={proxy_ip}')
# chrome_options.add_argument('--window-size=1920,1080')
# chrome_options.add_argument("--headless=new")
chrome_install = ChromeDriverManager().install()
folder = os.path.dirname(chrome_install)
chromedriver_path = os.path.join(folder, "chromedriver.exe")
service = ChromeService(chromedriver_path)



driver = webdriver.Chrome(service=service, options=chrome_options)



def upload_image_to_imgbb(image_path):
    # we need to upload payload' image as base64 string
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
            # Collect product links
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
                break  # No Next button means last page
            except Exception as e:
                print("Error clicking next:", e)
                break

    except Exception as e:
        print("Error loading page:", e)
        return []

    return links
 
def scrape_data(links):
    for link in links[2:4]:
        driver.get(link)
        time.sleep(5)
        try:
            SKUS_data=get_SKUS_data(driver)
            Products_data=get_product_data(driver)
            Imported_reviews_data=get_imported_reviews(driver)
        except Exception as e:
            print(f"Error scraping {link}: {e}")
            continue
    return SKUS_data,Products_data,Imported_reviews_data


def get_product_data(driver):
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
    
    except:
        product_name =""
    try:
        filter_categories_list = driver.find_elements(By.XPATH, "//nav[@aria-label='Breadcrumb']//a")
        filter_categories = ", ".join([filter_category.text.strip() for filter_category in filter_categories_list])
    except:
        filter_categories = ""
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
        product_sku = driver.current_url.split("/")[-1].split(".")[0]
    except:
        product_sku = ""

    try:
        try:
            # it doesnt exists till we scrall down a bit
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
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
        product_description = f"{description1_html}\n{description2_html}"

    except :
        product_description = ""

    try:
        product_name_with_sku = product_name + " " + driver.current_url.split("/")[-1].split(".")[0]
    except:
        product_name_with_sku = ""
    try:
        # model name can be found in product_name without the first word that is UA 
        model_name = product_name.split(" ", 1)[-1] if " " in product_name else product_name
    except:
        model_name = ""
    try:
        color_name = driver.find_element(By.XPATH, "//legend//span[@aria-hidden='true']").text.strip()
    except:
        color_name = ""
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
    except:
        percent_discount ="0%"
    
    
    size_chart_popup = driver.find_element(By.XPATH, "//button[.='Size & Fit Guide']")
    driver.execute_script("arguments[0].scrollIntoView(true);", size_chart_popup)
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -200);")
    time.sleep(1)
    size_chart_popup.click()
    time.sleep(1)
    try:
        size_chart_table = driver.find_element(By.XPATH, "(//div[@class='SizeChartModal_table-wrapper__8zKIq']//table)[1]")
        driver.execute_script("arguments[0].scrollIntoView(true);", size_chart_table)
        time.sleep(1)

        # save the screenshot as image to the size_charts folder with the sku
        if not os.path.exists("size_charts"):
            os.makedirs("size_charts")
        
        image_filename = f"size_chart_{product_sku}.png"
        image_path = os.path.join("size_charts", image_filename)
        driver.save_screenshot(image_path)
        size_chart_image_url=upload_image_to_imgbb(image_path)

    except:
        size_chart_image_url = ""
    try:
        size_chart_close_button = driver.find_element(By.XPATH, "(//div[@class='Dialog_dialog--ua-dialog--content__q_Y4K'])[1]//button[.='Close Dialog']")
        size_chart_close_button.click()
        time.sleep(1)
    except:
        pass
    try:
        sizes_available = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
        # bonus_filter = join all the sizes available with a comma
        bonus_filter = ", ".join([size.text.strip() for size in sizes_available])
    except:
        bonus_filter = ""
   

    scrape_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data={
        "Name": product_name_with_sku,
        "Source URL": product_source_url,
        "Coming Soon": product_coming_soon,
        "New Release": new_release,
        "Excluded from Discounts": exclude_from_discount,
        "SKU/Product ID": product_sku,
        "Description": description,
        "Product Description": product_description,
        "SEO Title Tag": product_name,
        "Product Brand or Title": "Under Armour",
        # "Model Name": model_name,
        "Color Name": color_name,
        "Price for Sorting": price_for_sorting,
        # "Fit": fit,
        "Percent Discount": percent_discount,
        "Size Guide": [{
            "url": size_chart_image_url,
        }],
        "Bonus/Filter 1": bonus_filter,
        # "Filter Category/ies": filter_categories,
        "Scraper Update": scrape_update,


    }
    Products_tab_data.append(data)
    return Products_tab_data
    

def get_SKUS_data(driver):
    time.sleep(2)
    try:
        h1_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'VariantDetailsEnhancedBuyPanel_productNameWording__')]")
        full_text = h1_element.text.strip()
        product_name = full_text.split('\n')[0].strip()  # Get only the first line
        color_name = driver.find_element(By.XPATH, "//legend//span[@aria-hidden='true']").text.strip()
        sku = driver.current_url.split("/")[-1].split(".")[0]
        name_of_product = f"{product_name} {color_name} {sku}"
    
    except:
        name_of_product = ""
    try:
        main_image_url = driver.find_element(By.XPATH, "(//div[@class='ProductImages_pdpImages__wK1mQ']//img)[1]").get_attribute("src")
    except:
        main_image_url = ""
    try:
        # get except the first image
        more_images_url = driver.find_elements(By.XPATH, "//div[@class='ProductImages_pdpImages__wK1mQ']//img")[1:]
        more_images_url = [image.get_attribute("src") for image in more_images_url]
    except:
        more_images_url = ""
    try:
        price_text=driver.find_element(By.XPATH, "(//span[@class='bfx-price bfx-list-price'])[2]").text.strip()
    except :
        price_text = ""
    try:
        # first $ comes price is like $89
        price_number = price_text.split("$")[1].strip()
    except:
        price_number = 0
    try:
        sizes_available = driver.find_elements(By.XPATH, "//div[@class='SizeSwatchesSection_size-swatches__WT8Z_ false']//div[@data-testid='size-swatch'][.//input[@data-orderable='true']]//span[contains(@id, 'size-label')]")
        # bonus_filter = join all the sizes available with a comma
        sizes= ", ".join([size.text.strip() for size in sizes_available])
    except:
        sizes= ""
    


    
        
    data={
        "Name": name_of_product,
        "Main Image": [{
            "url": main_image_url,
        }],
        "More Images": [{
            "url": url,
        } for url in more_images_url],
        "Price (Text)": price_text,
        "Price (Number)": int(price_number),
        "Price (Currency)": 0,
        "Sizes": sizes,

    }
    SKUS_tab_data.append(data)

    return SKUS_tab_data

def get_imported_reviews(driver):
    time.sleep(2)
    dialog_button = driver.find_element(By.XPATH, "(//button[contains(@class,'Dialog_close-button__LzXL1')])[5]")
    try:
        dialog_button.click()
        time.sleep(1)
    except (StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException):
        pass 
    try:
        h1_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'VariantDetailsEnhancedBuyPanel_productNameWording__')]")
        full_text = h1_element.text.strip()
        product_name = full_text.split('\n')[0].strip()  # Get only the first line
    
    except:
        product_name =""
    try:
        product_name_with_sku = product_name + " " + driver.current_url.split("/")[-1].split(".")[0]
    except:
        product_name_with_sku = ""
    try:
        records = at.get("Products", filter_by_formula=f"{{Name}} = '{product_name_with_sku}'")
        product_record_id = records["records"][0]["id"]
        print(product_record_id)
    except:
        product_record_id = None
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
        for review_person in review_frames:
            person_name_text = person_names[review_frames.index(review_person)].text.strip()
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
                img_urls = review_person.find_elements(By.XPATH, ".//img").get_attribute("src")
            except:
                img_urls = ""
                    
                    
            data ={
                "Name": person_name_text,
                "Product Reviewed": [product_record_id],
                "Date": date_reviewed.strftime('%Y-%m-%d'),
                "Review Title": review_title,
                "Review Comment": review_comment,
                "Rating": rating,
                "Review Image(s)": [{
                    "url": img_url,
                } for img_url in img_urls]
            }
            Imported_reviews_tab_data.append(data)
                
    except Exception as e:
        print(f"Error getting imported reviews: {e}")
    
        
    return Imported_reviews_tab_data
        


if __name__ == "__main__":
    # read links from product_links.txt if it exists
    if os.path.exists("product_links.txt"):
        with open("product_links.txt", "r") as file:
            links = [line.strip() for line in file.readlines()]

    Products_tab_data = []
    SKUS_tab_data = []
    Imported_reviews_tab_data = []
    # read the last 5 records from airtable "Products" table
    # last_5_records = at.get(table_name="Products", max_records=5)
    # print(last_5_records)
    SKUS_data,Products_data,Imported_reviews_data = scrape_data(links)
    print(SKUS_data)
    print(Products_data)
    print(Imported_reviews_data)
    # insert the Products data into airtable "Products" table

    for data in Products_data:
        at.create(table_name="Products", data=data)
    for data in SKUS_data:
        at.create(table_name="SKUs", data=data)
    for data in Imported_reviews_data:
        at.create(table_name="Imported Reviews", data=data)
 
    
    
    
    

    