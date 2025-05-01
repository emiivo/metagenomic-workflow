#!/bin/bash

# Define input and output files
PROJECT_FILE="accession.txt"
SRA_ACCESSION_FILE="sra_accessions.txt"
DOWNLOAD_DIR="../../inputs"
LOG_FILE="download.log"

# Log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== $(date) ==="


# Project accession from accession.txt
PROJECT_ID=$(cat "$PROJECT_FILE" | tr -d '[:space:]')

echo "Project ID: $PROJECT_ID"


mkdir -p "$DOWNLOAD_DIR"

# Check if SRA accession list exists
if [ -s "$SRA_ACCESSION_FILE" ]; then
    echo "SRA accession list exists."
else
    echo "Fetching SRA accession list for project: $PROJECT_ID"

    # SRA accession list
    esearch -db sra -query "$PROJECT_ID" | efetch -format runinfo | cut -d ',' -f1 | tail -n +2 > "$SRA_ACCESSION_FILE"

    # Check if file was created
    if [ -s "$SRA_ACCESSION_FILE" ]; then
        echo "SRA accessions saved to $SRA_ACCESSION_FILE"
    else
        echo "No accessions found."
        exit 1
    fi
fi

# Downloading files
echo "Starting downloads into $DOWNLOAD_DIR..."

while read -r ACCESSION; do
    FILE1="$DOWNLOAD_DIR/${ACCESSION}_1.fastq.gz"
    FILE2="$DOWNLOAD_DIR/${ACCESSION}_2.fastq.gz"

    # Check if files already exist
    if [[ -f "$FILE1" ]] || [[ -f "$FILE2" ]]; then
        echo "Files for $ACCESSION already exist. Skipping download."
        continue
    fi

    # Download using prefetch (fetches .sra file)
    echo "Prefetching $ACCESSION..."
    prefetch "$ACCESSION" --output-directory "$DOWNLOAD_DIR"

    # Convert .sra to fastq and compress
    echo "Converting to FASTQ and compressing..."
    fasterq-dump --split-files --progress -O "$DOWNLOAD_DIR" "$ACCESSION" && \
    pigz "$DOWNLOAD_DIR/${ACCESSION}_1.fastq" "$DOWNLOAD_DIR/${ACCESSION}_2.fastq"

    # Cleanup .sra file to save space
    rm -rf "$DOWNLOAD_DIR/$ACCESSION"

done < "$SRA_ACCESSION_FILE"

echo "Download complete! Files saved in $DOWNLOAD_DIR"

echo "=== $(date) ==="


