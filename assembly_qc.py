#!/usr/bin/env python3
import os
import time
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
GALAXY_URL = "https://usegalaxy.eu"
QUAST_TOOL_ID = "toolshed.g2.bx.psu.edu/repos/iuc/quast/quast/5.3.0+galaxy0"
CHECK_INTERVAL = 30  # seconds
LOG_FILE = "../outputs/galaxy/quast_metagenomic.log"

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

# MEGAHIT output datasets
history_contents = gi.histories.show_history(history_id, contents=True)
megahit_outputs = {
    item["name"]: item["id"]
    for item in history_contents
    if item["history_content_type"] == "dataset" and "MEGAHIT" in item["name"]
}

if not megahit_outputs:
    log("ERROR: No MEGAHIT outputs found.")
    exit(1)

log(f"Found MEGAHIT outputs: {list(megahit_outputs.keys())}")

# QUAST
submitted_jobs = []

for name, dataset_id in megahit_outputs.items():
    log(f"Processing file: '{name}'")

    dataset_info = gi.histories.show_dataset(history_id, dataset_id)
    if dataset_info["state"] != "ok":
        log(f"Skipping '{name}': Dataset not in 'ok' state.")
        continue

    log(f"Launching QUAST (metagenome mode) for '{name}'...")

    quast_inputs = {
    "mode|mode": "individual",
    "mode|in|custom": "false",
    "mode|in|inputs": { "src": "hda", "id": dataset_id },
    "assembly|type": "metagenome"
    }

    response = gi.tools.run_tool(
        history_id=history_id,
        tool_id=QUAST_TOOL_ID,
        tool_inputs=quast_inputs
    )

    output_ids = [output["id"] for output in response["outputs"]]
    log(f"  '{name}' - outputs: {output_ids}")

    submitted_jobs.extend(output_ids)

if not submitted_jobs:
    log("ERROR: No QUAST jobs were submitted.")
    exit(1)

# Check if it's completed
log(f"Waiting for {len(submitted_jobs)} QUAST job(s) to finish...")
while True:
    time.sleep(CHECK_INTERVAL)
    job_statuses = check_jobs_completion(gi, history_id, submitted_jobs)
    pending_jobs = [(dsid, state) for dsid, state, is_ok in job_statuses if not is_ok]
    for dsid, state, is_ok in job_statuses:
        log(f"  Dataset {dsid}: {state}")
    if not pending_jobs:
        break
    log(f"{len(pending_jobs)} job(s) still running...")

# Check final status
final_statuses = check_jobs_completion(gi, history_id, submitted_jobs)
failed = [dsid for dsid, state, is_ok in final_statuses if not is_ok]

if failed:
    log(f"ERROR: {len(failed)} QUAST job(s) failed: {failed}. Stop the script here if you want to change settings.")
    exit(1)

log("All QUAST jobs completed successfully!")
