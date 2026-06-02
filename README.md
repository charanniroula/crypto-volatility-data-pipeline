# Crypto Volatility Analytics Pipeline

## What This Project Does
This is an end-to-end project that automates the process of tracking crypto market swings. Instead of manually downloading spreadsheets or dealing with cluttered charts, I built a serverless cloud pipeline that automatically pulls hourly data for Bitcoin and Ethereum, calculates their exact price jumps, and displays them side-by-side in a clean visual dashboard.

## The Architecture & "The Why"
I chose these specific cloud-native tools to keep the system fast, scalable, and completely free to run:
* **Python & AWS Lambda:** I wrote a Python script to handle the API data extraction. Running it on AWS Lambda means it only fires up for a few seconds every hour to grab the data and then shuts down completely—saving massive compute costs.
* **Amazon S3:** This acts as the raw data pool. I set it up using a folder structure partitioned by date (`year/month/day`), which makes it organized and fast for tools to search through later.
* **Amazon EventBridge:** This acts as the automated alarm clock. Instead of me having to manually press "run" every hour, EventBridge fires a trigger precisely every 60 minutes to wake up the Lambda function.
* **Amazon Athena:** Instead of paying for a heavy, traditional SQL database server to hold this data, Athena lets me write standard SQL queries directly over the raw files sitting in S3. 
* **Tableau Public:** This is the final layer. It turns the clean SQL numbers into an interactive dashboard.

## How It Works

### 1. Grabbing the Data (Python / AWS Lambda)
The script hits a live crypto API (CoinGecko), cleans up the incoming format, adds a proper time stamp, and streams a clean data file straight into the S3 bucket.
* *Code Location:* `scripts/lambda_function.py`

### 2. Math & Analytics (AWS Athena / Presto SQL)
Because raw price points don't show volatility on their own, I used advanced SQL window functions to look exactly one hour backwards in time, separate the assets, and calculate the precise rate of change:
* *Code Location:* `athena_transform.sql`
