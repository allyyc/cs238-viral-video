from bs4 import BeautifulSoup
import json
import re
import requests
import time
import argparse
import pandas as pd
import os
import math

current_timestamp = int(time.time())

print("Current Unix timestamp:", current_timestamp)

def find_key_value(json_data, key):
    """
    Recursively search for a key in a nested JSON object and return its value.
    """
    if isinstance(json_data, dict):
        # If the key is found, return its value
        if key in json_data:
            return json_data[key]
        # Otherwise, recursively search in nested dictionaries
        for sub_key, sub_value in json_data.items():
            result = find_key_value(sub_value, key)
            if result is not None:
                return result
    elif isinstance(json_data, list):
        # If the JSON is a list, search each element
        for item in json_data:
            result = find_key_value(item, key)
            if result is not None:
                return result
    return None

# Path to the HTML file
file_path = "/Users/allisoncasasola/cs-328-final-project/raw/test.html"

account_url = "https://www.tiktok.com/@cs361finalproject?_t=8rvTLQdrQUg&_r=1"



def main():
    parser = argparse.ArgumentParser(description="Scrape data from multiple TikTok video page")
    parser.add_argument("data", help="input data file with links")

    args = parser.parse_args()

    # Read the input data file
    input_path = os.path.abspath(args.data)
    input_df = pd.read_csv(input_path)

    # Output path
    output_path = os.path.join(os.path.dirname(input_path), "extracted_data.csv")
    output_df = pd.read_csv(output_path)

    try:
        current_timestamp = int(time.time())

        output_urls = output_df["url"].tolist()

        for input_index, input_row in input_df.iterrows():
            if (input_row["url"] + " ") in output_urls:
                print(f"Data for row {input_index} already extracted.")
                time.sleep(1)
                continue

            url = input_row["url"]

            # Send an HTTP GET request to the URL
            response = requests.get(url)
            response.raise_for_status()

            # Read the HTML file
            content = response.text

            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Find the script tag or content that contains the "stats" data
            script_tag = soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")

            if script_tag and script_tag.string:
                # Load the content of the <script> tag as JSON
                try:
                    data = json.loads(script_tag.string)
                    print("JSON data successfully parsed!")
                    print(json.dumps(data, indent=2))  # Pretty-print the JSON
                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
            else:
                print("No <script> tag with the specified id or the tag is empty.")
            
            extract_data = {"createTime": None, "diggCount": None, "shareCount": None, "commentCount": None, "playCount": None, "collectCount": None}

            for key in extract_data:
                value = find_key_value(data, key)
                if value is not None:
                    extract_data[key] = value
                    print(f"Key '{key}' found with value '{value}'")   
                else:
                    print(f"Key '{key}' for url {url} not found in the JSON data.")

            if abs(int(extract_data["createTime"]) - current_timestamp) > 86400:
                print("Video is older than 1 days. Updating .CSV file.")
                    # add a new row to the output_df dataframe
                output_df.loc[len(output_df)] = [url + " ", extract_data["createTime"], extract_data["diggCount"], extract_data["shareCount"], extract_data["commentCount"], extract_data["playCount"], extract_data["collectCount"]]
        output_df.to_csv(output_path, index=False)

    except requests.RequestException as e:
        print(f"Failed to send an HTTP request: {e}")
            

if __name__ == "__main__":
    main()