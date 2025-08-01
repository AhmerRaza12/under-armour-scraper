#!/bin/bash

echo "🚀 Setting up Under Armour Scraper on Heroku..."

# Check if app name is provided
if [ -z "$1" ]; then
    echo "❌ Please provide an app name: ./deploy.sh your-app-name"
    exit 1
fi

APP_NAME=$1

echo "📦 Creating Heroku app: $APP_NAME"
heroku create $APP_NAME

echo "🔧 Adding buildpacks..."
heroku buildpacks:add heroku/python --app $APP_NAME
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chrome-for-testing --app $APP_NAME

echo "📅 Adding Scheduler add-on..."
heroku addons:create scheduler:standard --app $APP_NAME

echo "🔑 Setting up environment variables..."
echo "Please set your environment variables:"
echo "heroku config:set AIRTABLE_BASE=your_airtable_base_id --app $APP_NAME"
echo "heroku config:set AIRTABLE_TOKEN=your_airtable_api_token --app $APP_NAME"
echo "heroku config:set IMGBB_API_KEY=your_imgbb_api_key --app $APP_NAME"

echo "📤 Deploying to Heroku..."
git add .
git commit -m "Deploy Under Armour Scraper"
git push heroku main

echo "⚙️ Scaling worker dyno..."
heroku ps:scale worker=1 --app $APP_NAME

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set your environment variables using the commands above"
echo "2. Go to https://dashboard.heroku.com/apps/$APP_NAME/resources"
echo "3. Click on 'Scheduler' add-on"
echo "4. Add a new job with command: python daily_update.py"
echo "5. Set it to run daily at 1:00 AM Pacific Time"
echo ""
echo "🔍 Check logs: heroku logs --tail --app $APP_NAME" 