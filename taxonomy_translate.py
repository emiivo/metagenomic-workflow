#!/usr/bin/env python3
import os
import time
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
KRAKEN_TRANSLATE_TOOL_ID = "toolshed.g2.bx.psu.edu/repos/devteam/kraken_translate/kraken-translate/1.3.1"
CHECK_INTERVAL = 30  # seconds
LOG_FILE = "../outputs/galaxy/kraken_translate.log"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as logfile:
        logfile.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

def check_jobs_completion(gi, history_id, dataset_ids):
    statuses = []
    for dsid in dataset_ids:
        state = gi.histories.show_dataset(history_id, dsid)["state"]
        statuses.append((dsid, state, state == "ok"))
    return statuses

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

# Get datasets containing "Classification"
history_contents = gi.histories.show_history(history_id, contents=True)
classification_datasets = [
    item for item in history_contents
    if item["history_content_type"] == "dataset" and "Classification" in item["name"]
]

if not classification_datasets:
    log("ERROR: No datasets with 'Classification' found.")
    exit(1)

# Log the found datasets
log(f"Found Classification datasets:")
for item in classification_datasets:
    log(f"  {item['name']} (ID: {item['id']})")

# Find Kraken database
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

# Submit Kraken Translate
submitted_jobs = []
for item in classification_datasets:
    name = item["name"]
    dataset_id = item["id"]
    log(f"Submitting Kraken Translate for '{name}' (ID: {dataset_id})")

    dataset_info = gi.histories.show_dataset(history_id, dataset_id)
    
    # Find Kraken database from job parameters
    kraken_db = find_kraken_database(dataset_info)
    
    if not kraken_db:
        log(f"  ERROR: Could not determine Kraken database for '{name}' (ID: {dataset_id}).")
        continue

    inputs = {
        "kraken_database": kraken_db,
        "input": { "src": "hda", "id": dataset_id }
    }

    response = gi.tools.run_tool(
        history_id=history_id,
        tool_id=KRAKEN_TRANSLATE_TOOL_ID,
        tool_inputs=inputs
    )

    output_ids = [output["id"] for output in response["outputs"]]
    log(f"  Submitted job for '{name}' (ID: {dataset_id}) -> Outputs: {output_ids}")
    submitted_jobs.extend(output_ids)

# Check if it's completed
if not submitted_jobs:
    log("ERROR: No Kraken Translate jobs were submitted.")
    exit(1)

log(f"Waiting for {len(submitted_jobs)} Kraken Translate job(s) to finish...")
while True:
    time.sleep(CHECK_INTERVAL)
    job_statuses = check_jobs_completion(gi, history_id, submitted_jobs)
    pending_jobs = [(dsid, state) for dsid, state, is_ok in job_statuses if not is_ok]
    for dsid, state, is_ok in job_statuses:
        log(f"  Dataset {dsid}: {state}")
    if not pending_jobs:
        break
    log(f"{len(pending_jobs)} job(s) still running...")

# Final check
final_statuses = check_jobs_completion(gi, history_id, submitted_jobs)
failed = [dsid for dsid, state, is_ok in final_statuses if not is_ok]

if failed:
    log(f"ERROR: {len(failed)} Kraken Translate job(s) failed: {failed}")
    exit(1)

log("All Kraken Translate jobs completed successfully!")

