#!/bin/bash

# Define input and output files
PROJECT_FILE="accession.txt"
SRA_ACCESSION_FILE="sra_accessions.txt"
DOWNLOAD_DIR="../inputs"

# Read the project accession from accession.txt
PROJECT_ID=$(cat "$PROJECT_FILE" | tr -d '[:space:]')

echo "Project ID: $PROJECT_ID"

# Ensure download directory exists
mkdir -p "$DOWNLOAD_DIR"

# Check if SRA accession list exists
if [ -s "$SRA_ACCESSION_FILE" ]; then
    echo "SRA accession list exists. Skipping retrieval."
else
    echo "Fetching SRA accession list for project: $PROJECT_ID"

    # Retrieve SRA accessions and save to separate file
    esearch -db sra -query "$PROJECT_ID" | efetch -format runinfo | cut -d ',' -f1 | tail -n +2 > "$SRA_ACCESSION_FILE"

    # Check if file was created
    if [ -s "$SRA_ACCESSION_FILE" ]; then
        echo "SRA accessions saved to $SRA_ACCESSION_FILE"
    else
        echo "Error: No accessions found. Check the project ID."
        exit 1
    fi
fi

# Download SRA data using fasterq-dump into ../inputs/
echo "Starting downloads into $DOWNLOAD_DIR..."
# cat "$SRA_ACCESSION_FILE" | xargs -I {} fasterq-dump --split-files --progress -O "$DOWNLOAD_DIR" {}

echo "Download complete! Files saved in $DOWNLOAD_DIR"

