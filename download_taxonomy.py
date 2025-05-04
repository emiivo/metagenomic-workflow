#!/usr/bin/env python3
import os
import time
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
OUTPUT_DIR = "../outputs/taxonomy/translated_kraken"
LOG_FILE = "../outputs/galaxy/kraken_translate_download.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as logfile:
        logfile.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

def find_kraken_database(dataset_info):
    job_id = dataset_info.get('creating_job')
    if job_id:
        job_info = gi.jobs.show_job(job_id)
        log(f"Job info: {job_info}")
        
        job_params = job_info.get('params', {})
        log(f"Job params: {job_params}")
        
        kraken_db = job_params.get('kraken_database')
        if kraken_db:
            # Remove spaces and quotes
            kraken_db = kraken_db.strip().strip('"')
            log(f"  Found Kraken database: {kraken_db}")
            return kraken_db
        else:
            log("  ERROR: Kraken database not found in job params.")
    else:
        log(f"  ERROR: No job information found for dataset {dataset_info['name']}.")

    return None

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

# Get datasets containing "Kraken-translate"
history_contents = gi.histories.show_history(history_id, contents=True)
kraken_translate_datasets = [
    item for item in history_contents
    if item["history_content_type"] == "dataset" and "Kraken-translate" in item["name"]
]

if not kraken_translate_datasets:
    log("ERROR: No datasets with 'Kraken-translate' found.")
    exit(1)

log(f"Found Kraken-translate datasets:")
for item in kraken_translate_datasets:
    log(f"  {item['name']} (ID: {item['id']})")

# Process and download Kraken databases
for item in kraken_translate_datasets:
    name = item["name"]
    dataset_id = item["id"]
    log(f"Processing Kraken-translate dataset '{name}' (ID: {dataset_id})")

    dataset_info = gi.histories.show_dataset(history_id, dataset_id)

    # Check the state
    state = dataset_info.get("state")
    if state != "ok":
        log(f"  Skipping dataset '{name}' (ID: {dataset_id}) (current state: {state}).")
        continue
    
    # Find Kraken database
    kraken_db = find_kraken_database(dataset_info)
    
    if not kraken_db:
        log(f"  ERROR: Could not determine Kraken database for '{name}' \
            (ID: {dataset_id}).")
        continue
    
    # Create directory
    db_output_dir = os.path.join(OUTPUT_DIR, kraken_db)
    os.makedirs(db_output_dir, exist_ok=True)
    log(f"  Created directory for Kraken database: {db_output_dir}")

    # Download the dataset
    gi.datasets.download_dataset(dataset_id, db_output_dir)
    log(f"  Downloaded Kraken database '{kraken_db}' as .tabular to {db_output_dir}")

log("All Kraken-translate datasets processed successfully!")

