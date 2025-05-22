#!/usr/bin/env python3
import os, time, re
from datetime import datetime
from bioblend.galaxy import GalaxyInstance

API_KEY_FILE = "galaxy/key.txt"
ACCESSION_FILE = "download/accession.txt"
FTP_FILES_DIR = "../outputs/fastq_trimmed"
GALAXY_URL = "https://usegalaxy.eu"
MEGAHIT_TOOL_ID = "toolshed.g2.bx.psu.edu/repos/iuc/megahit/megahit/1.2.9+galaxy2"
CHECK_INTERVAL = 30 # seconds
LOG_FILE = "../outputs/galaxy/megahit_paired.log"

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE,"a") as f: f.write(f"{ts} {msg}\n")
    print(f"{ts} {msg}")

def all_done(gi, hid, ids):
    out=[]
    for dsid in ids:
        st = gi.histories.show_dataset(hid, dsid)["state"]
        out.append((dsid, st, st=="ok"))
    return out

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
    log(f"ERROR: history '{history_name}' not found.")
    exit(1)
hid = histories[0]["id"]
log(f"Using history '{history_name}' (ID: {hid})")

# Check uploaded files
ftp_files = [f for f in os.listdir(FTP_FILES_DIR) if f.endswith(".fastq.gz")]
if not ftp_files:
    log(f"ERROR: no .fastq.gz in {FTP_FILES_DIR}"); exit(1)
log(f"Looking for uploaded files: {ftp_files}")

# Build map filename to dataset ID
contents = gi.histories.show_history(hid, contents=True)
name2id = { item["name"]: item["id"]
            for item in contents
            if item["history_content_type"]=="dataset"
            and item["name"] in ftp_files }

# Verify if all ids are found
missing = set(ftp_files) - set(name2id)
if missing:
    log(f"ERROR: these uploaded files not found in history: {sorted(missing)}")
    exit(1)

# Group into pairs by base name
pairs = {}
pattern = re.compile(r"^(.+?)[._-]([12])\.fastq\.gz$", re.IGNORECASE)
for fn, dsid in name2id.items():
    m = pattern.match(fn)
    if not m:
        log(f"WARNING: filename {fn} does not match *_1.fastq.gz or *_2.fastq.gz pattern; skipping")
        continue
    base, num = m.groups()
    side = "forward" if num=="1" else "reverse"
    pairs.setdefault(base, {})[side] = dsid

# MEGAHIT
jobs = []
for sample, ids in pairs.items():
    fwd = ids.get("forward")
    rev = ids.get("reverse")
    if not (fwd and rev):
        log(f"Skipping '{sample}': incomplete pair ({list(ids)})")
        continue

    # double-check both still OK
    if gi.histories.show_dataset(hid, fwd)["state"] != "ok" or \
       gi.histories.show_dataset(hid, rev)["state"] != "ok":
        log(f"Skipping '{sample}': one of the datasets is not in state 'ok'")
        continue

    log(f"Launching MEGAHIT (paired) for '{sample}'…")
    inputs = {
        "input_option|choice": "paired",
        "input_option|fastq_input1": [ {"src":"hda","id":fwd} ],
        "input_option|fastq_input2": [ {"src":"hda","id":rev} ],
    }
    resp = gi.tools.run_tool(
        history_id   = hid,
        tool_id      = MEGAHIT_TOOL_ID,
        tool_inputs  = inputs,
        input_format = "legacy"
    )
    out_ids = [o["id"] for o in resp["outputs"]]
    log(f"  '{sample}' - outputs: {out_ids}")
    jobs.extend(out_ids)

if not jobs:
    log("ERROR: no MEGAHIT jobs submitted."); exit(1)

# Check if it's completed
log(f"Waiting for {len(jobs)} jobs to finish…")
while True:
    time.sleep(CHECK_INTERVAL)
    status  = all_done(gi, hid, jobs)
    pending = [(d,s) for (d,s,ok) in status if not ok]
    for d,s,ok in status:
        log(f"  {d}: {s}")
    if not pending:
        break
    log(f"{len(pending)} still running…")

log("All paired‐end MEGAHIT runs completed!")
