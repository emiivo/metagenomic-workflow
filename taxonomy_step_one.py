#!/usr/bin/env python3
import os
import time
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
DATABASES_FILE = "galaxy/databases.txt"
GALAXY_URL = "https://usegalaxy.eu"
KRAKEN_TOOL_ID = "toolshed.g2.bx.psu.edu/repos/devteam/kraken/kraken/1.3.1"
CHECK_INTERVAL = 30  # seconds
LOG_FILE = "../outputs/galaxy/kraken_taxonomy.log"

DATABASE_OPTIONS = {
    "V": "Viral",
    "B": "Bacteria",
    "P": "Plasmid",
    "A": "Archaea"
}

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

def get_user_databases():
    while True:
        print("\nSelect Kraken databases to use:")
        print("  V = Viral")
        print("  B = Bacteria")
        print("  P = Plasmid")
        print("  A = Archaea")
        choice = input("Enter one or more: ").upper().replace(" ", "")
        selected = [DATABASE_OPTIONS[c] for c in choice if c in DATABASE_OPTIONS]
        if selected and len(selected) == len(set(choice)):
            with open(DATABASES_FILE, "w") as dbfile:
                dbfile.write(" ".join(selected) + "\n")
            return selected
        print("Invalid input. Please enter only V, B, P, or A.")

# Validate input files
if not os.path.exists(API_KEY_FILE) or not os.path.exists(ACCESSION_FILE):
    log("ERROR: Missing API key or accession file.")
    exit(1)

# Get credentials
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

# Get MEGAHIT outputs
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

# Get database selection
databases = get_user_databases()
log(f"Selected databases: {databases}")

# Run Kraken for each database
submitted_jobs = []

for name, dataset_id in megahit_outputs.items():
    dataset_info = gi.histories.show_dataset(history_id, dataset_id)
    if dataset_info["state"] != "ok":
        log(f"Skipping '{name}': Dataset not in 'ok' state.")
        continue

    for db in databases:
        log(f"Launching Kraken for '{name}' using database '{db}'...")

        kraken_inputs = {
            "mode|mode": "individual",
            "kraken_database": db,
            "split_reads": True,
            "single_paired|input_sequences": {
                "src": "hda",
                "id": dataset_id
            }
        }

        try:
            response = gi.tools.run_tool(
                history_id=history_id,
                tool_id=KRAKEN_TOOL_ID,
                tool_inputs=kraken_inputs
            )
            output_ids = [output["id"] for output in response["outputs"]]
            log(f"  '{name}' with '{db}' -> outputs: {output_ids}")
            submitted_jobs.extend(output_ids)
        except Exception as e:
            log(f"  ERROR running Kraken on '{name}' with '{db}': {e}")

if not submitted_jobs:
    log("ERROR: No Kraken jobs were submitted.")
    exit(1)

# Check if it's completed
log(f"Waiting for {len(submitted_jobs)} Kraken job(s) to finish...")
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
    log(f"ERROR: {len(failed)} Kraken job(s) failed: {failed}.")
    exit(1)

log("All Kraken jobs completed successfully!")

