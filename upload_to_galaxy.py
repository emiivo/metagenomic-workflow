#!/usr/bin/env python3

import os
import time
from bioblend.galaxy import GalaxyInstance
from datetime import datetime

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
FTP_DIR = "/"
UPLOAD_LOG_FILE = "../outputs/galaxy/upload_from_ftp.log"
FTP_FILES_DIR = "../outputs/fastq_trimmed"
INTERVAL = 10  # 10 seconds

# Log
def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(UPLOAD_LOG_FILE, "a") as f:
        f.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

# API
if not os.path.exists(API_KEY_FILE):
    log(f"ERROR: Galaxy API key file not found: {API_KEY_FILE}")
    exit(1)

with open(API_KEY_FILE) as f:
    api_key = f.read().strip()

# History name
if not os.path.exists(ACCESSION_FILE):
    log(f"ERROR: Accession file not found: {ACCESSION_FILE}")
    exit(1)

with open(ACCESSION_FILE) as f:
    history_name = f.read().strip()

# Galaxy Instance
gi = GalaxyInstance(url=GALAXY_URL, key=api_key)

# Find or Create History
histories = gi.histories.get_histories(name=history_name)
if histories:
    history_id = histories[0]['id']
    log(f"Using existing history: {history_name} (ID: {history_id})")
else:
    history = gi.histories.create_history(name=history_name)
    history_id = history['id']
    log(f"Created new history: {history_name} (ID: {history_id})")

# Upload Files from FTP
ftp_files = [f for f in os.listdir(FTP_FILES_DIR) if f.endswith(".fastq.gz")]
if not ftp_files:
    log(f"WARNING: No .fastq.gz files found in {FTP_FILES_DIR}")
    exit(0)

dataset_ids = []

for filename in ftp_files:
    try:
        upload_response = gi.tools.upload_from_ftp(path=filename, history_id=history_id)

        # Handle single and multiple outputs
        if isinstance(upload_response, dict) and 'outputs' in upload_response:
            outputs = upload_response['outputs']
        elif isinstance(upload_response, list):
            outputs = upload_response
        else:
            outputs = [upload_response]

        for dataset in outputs:
            if isinstance(dataset, dict) and 'id' in dataset:
                dataset_ids.append(dataset['id'])
                log(f"Started upload for {filename}, dataset ID: {dataset['id']}")
            else:
                log(f"WARNING: Unexpected dataset format for {filename}: {dataset}")
    except Exception as e:
        log(f"ERROR uploading {filename}: {e}")


# Wait for Uploads
log("Waiting for uploads to complete...")

def is_upload_done(ds):
    return ds['state'] == 'ok'


def all_done(ids):
    statuses = []
    for ds_id in ids:
        try:
            ds = gi.histories.show_dataset(history_id, ds_id)
            done = is_upload_done(ds)
            statuses.append((ds_id, ds['state'], done))
        except Exception as e:
            statuses.append((ds_id, f"error ({e})", False))
    return statuses

done = False
while not done:
    time.sleep(INTERVAL)
    statuses = all_done(dataset_ids)
    not_done = [(dsid, state) for dsid, state, finished in statuses if not finished]
    for dsid, state, finished in statuses:
        log(f"Dataset {dsid} state: {state} {'(done)' if finished else '(waiting)'}")
    if not not_done:
        done = True
        log("All uploads completed successfully.")
    else:
        log(f"{len(not_done)} uploads still in progress...")


