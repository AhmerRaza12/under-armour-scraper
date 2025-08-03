#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import airtable

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
at = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

def debug_urls():
    """Debug URL matching issues"""
    print("🔍 Debugging URL matching...")
    
    # Read URLs from file
    if os.path.exists("scraped_product_links.txt"):
        with open("scraped_product_links.txt", "r") as file:
            file_urls = [line.strip() for line in file.readlines() if line.strip()]
        print(f"📄 URLs in file: {len(file_urls)}")
        for i, url in enumerate(file_urls[:5]):  # Show first 5
            print(f"  {i+1}. {url}")
    else:
        print("❌ scraped_product_links.txt not found")
        return
    
    # Get URLs from Airtable
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
        
        print(f"📊 Total products in Airtable: {len(all_products)}")
        
        airtable_urls = []
        for product in all_products:
            source_url = product.get("fields", {}).get("Source URL", "")
            if source_url:
                airtable_urls.append({
                    "id": product["id"],
                    "name": product.get("fields", {}).get("Name", "Unknown"),
                    "url": source_url
                })
        
        print(f"\n🗄️ URLs in Airtable: {len(airtable_urls)}")
        for i, item in enumerate(airtable_urls[:5]):  # Show first 5
            print(f"  {i+1}. {item['name']} -> {item['url']}")
        
        # Try to match URLs
        print(f"\n🔗 Testing URL matching...")
        for file_url in file_urls[:3]:  # Test first 3
            print(f"\nLooking for: {file_url}")
            found = False
            for airtable_item in airtable_urls:
                if airtable_item["url"] == file_url:
                    print(f"✅ MATCH: {airtable_item['name']}")
                    found = True
                    break
                elif airtable_item["url"].rstrip('/') == file_url.rstrip('/'):
                    print(f"⚠️  PARTIAL MATCH (trailing slash): {airtable_item['name']}")
                    print(f"   File: '{file_url}'")
                    print(f"   Airtable: '{airtable_item['url']}'")
                    found = True
                    break
            if not found:
                print(f"❌ NO MATCH FOUND")
                # Show similar URLs
                for airtable_item in airtable_urls:
                    if file_url.split('/')[-1] in airtable_item["url"]:
                        print(f"   Similar: {airtable_item['name']} -> {airtable_item['url']}")
        
    except Exception as e:
        print(f"❌ Error getting Airtable data: {e}")

if __name__ == "__main__":
    debug_urls() 