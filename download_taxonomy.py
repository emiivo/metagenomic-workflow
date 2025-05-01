#!/usr/bin/env python3
import os
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
OUTPUT_DIR = "../outputs/taxonomy"
LOG_FILE = "../outputs/galaxy/kraken_translate_download.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as logfile:
        logfile.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

if not os.path.exists(API_KEY_FILE) or not os.path.exists(ACCESSION_FILE):
    log("ERROR: Missing API key or accession file.")
    exit(1)

with open(API_KEY_FILE, "r") as key_file:
    api_key = key_file.read().strip()

with open(ACCESSION_FILE, "r") as accession_file:
    history_name = accession_file.read().strip()

gi = GalaxyInstance(GALAXY_URL, api_key)

# Retrieve the specified history
histories = gi.histories.get_histories(name=history_name)
if not histories:
    log(f"ERROR: History '{history_name}' not found.")
    exit(1)
history_id = histories[0]["id"]
log(f"Using history '{history_name}' (ID: {history_id})")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Find datasets
history_contents = gi.histories.show_history(history_id, contents=True)
translated_datasets = [
    item for item in history_contents
    if item["history_content_type"] == "dataset" and "Translated" in item["name"]
]

if not translated_datasets:
    log("ERROR: No 'Translated' datasets found in history.")
    exit(1)

log(f"Found {len(translated_datasets)} translated dataset(s). Starting download...")

# Download each dataset
for item in translated_datasets:
    try:
        dataset_id = item["id"]
        name = item["name"]
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name)
        local_path = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")

        gi.dataset

