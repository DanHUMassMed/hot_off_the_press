#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime, timedelta
import csv

from dotenv import load_dotenv

from pub_worm.ncbi.entreze_api import EntrezAPI
from pub_worm.biorxiv.biorxiv_api import biorxiv_search

class PublishHistory:
    def __init__(self, csv_filename='pub_hist.csv'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_filename = os.path.join(script_dir, csv_filename)
        
        self.max_rows = 100
        self.data = []

        self._read_csv()

    def _read_csv(self):
        try:
            with open(self.csv_filename, mode='r') as file:
                reader = csv.DictReader(file)
                self.data = list(reader)
        except FileNotFoundError:
            # If the file does not exist, start with an empty data list
            self.data = []

    def _write_csv(self):
        # Write the data back to the CSV, maintaining date order
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['url', 'date'])
            writer.writeheader()
            writer.writerows(self.data)

    def add_new(self, url):
        # Add the new URL with today's date
        today = datetime.today().strftime('%Y-%m-%d')
        new_entry = {'url': url, 'date': today}

        # Check if the URL is already in the history
        if not self.has_url(url):
            self.data.append(new_entry)

            # Sort the list by date (ascending)
            self.data.sort(key=lambda x: x['date'])

            # If there are more than 100 rows, remove the oldest
            if len(self.data) > self.max_rows:
                self.data = self.data[-self.max_rows:]

            # Write the updated data back to the CSV
            self._write_csv()

    def has_url(self, url):
        # Check if the URL is in the CSV
        return any(row['url'] == url for row in self.data)

def post_to_slack1(new_title, new_url, slack_webhook):
    slack_webhook_url=f"https://hooks.slack.com/services/{slack_webhook}"
    message = f"*{new_title}*\n{new_url}"
    slack_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    }

    response = requests.post(slack_webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
    
    if response.status_code != 200:
        raise Exception(f"Slack API request failed with status code {response.status_code}")


def post_to_slack(new_title, new_url, slack_webhook):
    message = f"*{new_title}*\n{new_url}"
    print(message)
    
    
if __name__ == "__main__":
    load_dotenv()
    publish_istory_db = PublishHistory()
    slack_webhook = os.getenv('slack_webhook')

    new_biorxiv_entries = biorxiv_search(days=2)
    for entry in new_biorxiv_entries:
        new_title = entry.get('title','')
        new_url   = entry.get('url','')
        if new_title and new_url:
            if not publish_istory_db.has_url(new_url):
                post_to_slack(new_title, new_url, slack_webhook)
                publish_istory_db.add_new(new_url)
    
    term = "C. elegans"
    days=1 # Current day only
    today = datetime.today()
    start_date = (today - timedelta(days=days)).strftime('%Y/%m/%d')
    end_date = today.strftime('%Y/%m/%d')

    search_term = f"{term} AND ({start_date}[PDAT] : {end_date}[PDAT])"

    ncbi_api = EntrezAPI()
    esearch_params = {'term': search_term }
    esearch_result = ncbi_api.entreze_esearch(esearch_params)
    efetch_result = ncbi_api.entreze_efetch(esearch_result)
    
    for entry in efetch_result['articles']:
        new_title = entry.get('title','')
        new_url   = entry.get('doi','')
        if new_title and new_url:
            new_url = f"https://doi.org/{new_url}"
            if not publish_istory_db.has_url(new_url):
                post_to_slack(new_title, new_url, slack_webhook)
                publish_istory_db.add_new(new_url)
