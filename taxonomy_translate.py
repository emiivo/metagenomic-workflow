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
classification_datasets = {
    item["name"]: item["id"]
    for item in history_contents
    if item["history_content_type"] == "dataset" and "Classification" in item["name"]
}

if not classification_datasets:
    log("ERROR: No datasets with 'Classification' found.")
    exit(1)

log(f"Found Classification datasets: {list(classification_datasets.keys())}")

# Submit Kraken Translate jobs
submitted_jobs = []
for name, dataset_id in classification_datasets.items():
    log(f"Submitting Kraken Translate for '{name}'")

    dataset_info = gi.histories.show_dataset(history_id, dataset_id)
    job_id = dataset_info.get("creating_job")

    if not job_id:
        log(f"  ERROR: Could not find creating job for '{name}'.")
        continue

    try:
        job_info = gi.jobs.show_job(job_id)
        kraken_inputs = job_info.get("inputs", {})
        kraken_db = kraken_inputs.get("kraken_database", {}).get("value")

        if not kraken_db:
            log(f"  ERROR: Could not determine Kraken database for '{name}'.")
            continue

        log(f"  Detected Kraken database: {kraken_db}")

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
        log(f"  Submitted job for '{name}' -> Outputs: {output_ids}")
        submitted_jobs.extend(output_ids)

    except Exception as e:
        log(f"  ERROR submitting Kraken Translate for '{name}': {e}")

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
        log(f"  Dataset {dsid}: {state}{''}")
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

