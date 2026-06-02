import datetime # reading the computer's clock
import pandas as pd 
import requests
import os # needed to store data into csv file
import boto3 # AWS tool allowing Python to talk to S3

# For AWS Lambda
def lambda_handler(event, context):
    
    # pipeline settings 
    # Bucket created on S3
    BUCKET_NAME = "crypto-data-charan" 
   # FILE_NAME = "data/crypto_data.csv"

    # Writing file to temporary storage in Lambda RAM
    LOCAL_TEMP_PATH = "/tmp/crypto_data.csv"

    # Tell S3 to place it inside the 'data/' folder structure in the cloud
    S3_KEY = "data/crypto_data.csv"

    # firing up S3 client bridge
    s3_client = boto3.client('s3')

    # Get's the current time right now
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if file already exists on S3
    file_exists = True
    try:
        s3_client.head_object(Bucket=BUCKET_NAME, Key=S3_KEY)
        print("Pipeline Status: S3 file found. Incrementing hourly append.")
    except:
        file_exists = False
        print("Pipeline Status: N/A. Adding 30 days data.")

    cleaned_rows = []

    # If file does not exist, backfill 30 days of data
    if not file_exists:

        # Loop to go thru each coin and fetch 30 days of data
        for coin_id in ["bitcoin", "ethereum"]:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
            response = requests.get(url)
            data = response.json()

            # This is the data we need from the API call
            prices = data["prices"]
            market_caps = data["market_caps"]
            volumes = data["total_volumes"]

            # Loop to go thru each row and fetch the exact numbers from the api
            # Loop thru every individual timestamp
            for i in range(len(prices)):
                timestamp_ms = prices[i][0]
                # Converting milliseconds to seconds then to readable time
                readable_time = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")

                # Building a dictionary with the data we want
                # Structure the single historical row for this specific hour and asset
                row = {
                    "timestamp": readable_time,
                    "asset_id": coin_id.upper(),
                    "price_usd": prices[i][1],
                    "market_cap_usd": market_caps[i][1],
                    "volume_24h_usd": volumes[i][1]
                }
                cleaned_rows.append(row)

        df = pd.DataFrame(cleaned_rows)
        df = df.sort_values(by="timestamp")

        # Save fresh with headers
        df.to_csv(LOCAL_TEMP_PATH, index=False)
        s3_client.upload_file(LOCAL_TEMP_PATH, BUCKET_NAME, S3_KEY)
        return {'statusCode': 200, 'body': f'Backfill Complete! Generated {len(df)} historical rows.'}

    # If file exists, get latest data and append
    else:

        # Got this api URL by going to coingecko url
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true"

        # Fetching the data from the URL and saved in variable 'response'
        response = requests.get(url)

        # json() turns it into type dict which has key, value
        crypto_dictionary = response.json()

        #Loop to go thru each row and fetch the exact numbers from btc and eth
        for coin_id in ["bitcoin", "ethereum"]:

            metrics = crypto_dictionary[coin_id]

            row = {
                "timestamp": current_time,
                "asset_id": coin_id.upper(),
                "price_usd": metrics["usd"], # Find's it where it equals "usd" on the json file
                "market_cap_usd": metrics["usd_market_cap"],
                "volume_24h_usd": metrics["usd_24h_vol"],
            }

            # appending the row data into cleaned_rows
            cleaned_rows.append(row)

    # Built in function from Pandas that organizes the data
        df = pd.DataFrame(cleaned_rows)

        # If file exists, download it to temp storage
        s3_client.download_file(BUCKET_NAME, S3_KEY, LOCAL_TEMP_PATH)

        # changing mode to a for append b/c default is w for write
        df.to_csv(LOCAL_TEMP_PATH, mode='a', header=False, index=False) 

        # Upload the file from Lambda's temp storage to S3
        s3_client.upload_file(LOCAL_TEMP_PATH, BUCKET_NAME, S3_KEY)

    return {
        'statusCode': 200,
        'body': 'Hourly Data successfully piped to S3'
    }
