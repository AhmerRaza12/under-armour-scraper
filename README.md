# Under Armour Scraper

A Python-based web scraper for Under Armour products with daily automated updates.

## Features

- Scrapes product information from Under Armour website
- Stores data in Airtable with Products, SKUs, and Customer Reviews tables
- Daily automated updates at 1am Pacific Time
- Heroku deployment ready

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```
AIRTABLE_BASE=your_airtable_base_id
AIRTABLE_TOKEN=your_airtable_api_token
IMGBB_API_KEY=your_imgbb_api_key
```

3. Run the scraper:
```bash
python under_armour_scraper.py
```

### Heroku Deployment

1. Create a new Heroku app:
```bash
heroku create your-app-name
```

2. Add buildpacks:
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chrome-for-testing
```

3. Add the Scheduler add-on:
```bash
heroku addons:create scheduler:standard
```

4. Set environment variables:
```bash
heroku config:set AIRTABLE_BASE=your_airtable_base_id
heroku config:set AIRTABLE_TOKEN=your_airtable_api_token
heroku config:set IMGBB_API_KEY=your_imgbb_api_key
```

5. Deploy to Heroku:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

6. Scale the worker dyno:
```bash
heroku ps:scale worker=1
```

7. Set up the scheduler job:
   - Go to your Heroku dashboard
   - Navigate to the Scheduler add-on
   - Add a new job with the command: `python daily_update.py`
   - Set it to run daily at 1:00 AM Pacific Time

## File Structure

- `under_armour_scraper.py` - Main scraper for new products (skips already scraped products)
- `daily_update.py` - Script for updating existing products
- `scheduler.py` - Scheduler for automated daily updates
- `startup.py` - Startup script that runs initial scraping then scheduler
- `scraped_product_links.txt` - List of product URLs that have been scraped
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku process configuration
- `app.json` - Heroku app configuration
- `runtime.txt` - Python version specification

## Airtable Tables

### Products Table
- Name
- Source URL
- Coming Soon
- New Release
- Excluded from Discounts
- SKU/Product ID
- Description
- Product Description
- SEO Title Tag
- Product Brand or Title
- Size Guide
- Model Name
- Color Name
- Price for Sorting
- Percent Discount
- Scraper Update
- Brand
- SKUs (linked to SKUs table)
- Filter Category/ies
- Bonus/Filter 1-30

### SKUs Table
- Name
- Products (product name)
- MSRP
- Actual Price
- Price (Currency)
- Sizes
- SKU Values (Text)
- SKU/Product ID
- Main Image
- More Images

### Customer Reviews Table
- Name
- Product Reviewed (linked to Products table)
- Date
- Review Title
- Review Comment
- Rating
- Review Image(s)

## Daily Updates

The system automatically updates the following fields daily at 1am Pacific Time:

### Products Table:
- Coming Soon
- New Release
- Excluded from Discounts
- Price for Sorting
- Percent Discount
- Bonus/Filter 1-30
- Scraper Update

### SKUs Table:
- MSRP
- Actual Price
- Sizes

## Usage

1. **Initial Scraping**: Run `python under_armour_scraper.py` to scrape new products (skips already scraped ones)
2. **Use Existing Products**: Run `python under_armour_scraper.py --existing` to process already scraped products
3. **Daily Updates**: The scheduler automatically runs `daily_update.py` daily at 1am Pacific Time
4. **Manual Updates**: You can run `python daily_update.py` manually to update products
5. **Full Startup**: Run `python startup.py` to scrape new products then start scheduler

## Troubleshooting

### Heroku Issues
- Check logs: `heroku logs --tail`
- Restart dyno: `heroku restart`
- Check dyno status: `heroku ps`

### Environment Variables
- Verify all environment variables are set: `heroku config`
- Update variables: `heroku config:set VARIABLE_NAME=value`

### Scheduler Issues
- Check scheduler logs in Heroku dashboard
- Verify the job command is correct: `python daily_update.py`
- Ensure the timezone is set to Pacific Time

## Notes

- The scraper uses Selenium with Chrome in headless mode
- Images are uploaded to ImgBB for storage
- All timestamps are in Pacific Time
- The system respects rate limits and includes delays between requests 