#!/usr/bin/env python3

import os
import zipfile
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
DOWNLOAD_DIR = "../outputs/galaxy/quast_downloads"
LOG_FILE = "../outputs/galaxy/quast_download.log"

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

history_contents = gi.histories.show_history(history_id, contents=True)
quast_outputs = {
    item["name"]: item["id"]
    for item in history_contents
    if item["history_content_type"] == "dataset" and "Quast" in item["name"]
}

if not quast_outputs:
    log("ERROR: No QUAST outputs found.")
    exit(1)

log(f"Found QUAST outputs: {list(quast_outputs.keys())}")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

downloaded_files = []
for name, dataset_id in quast_outputs.items():
    filename = os.path.join(DOWNLOAD_DIR, dataset_id)
    log(f"Attempting to download dataset '{name}' (ID: {dataset_id}) to '{filename}'...")
    try:
        gi.datasets.download_dataset(dataset_id, file_path=filename, use_default_filename=False)
        log(f"Successfully downloaded dataset ID '{dataset_id}'")
        downloaded_files.append((filename, dataset_id))
    except Exception as e:
        log(f"ERROR downloading dataset ID '{dataset_id}': {e}")

log("Download script completed.")

