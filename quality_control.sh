#!/bin/bash

LOG_FILE="../outputs/quality_control.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== $(date) ==="

# FastQC
for file1 in ../inputs/*_1.fastq.gz; do
    file2="${file1/_1/_2}"
    accession=$(basename "$file1" _1.fastq.gz)
    output_dir="../outputs/fastqc/$accession"
    mkdir -p "$output_dir"

    echo "Running FastQC for: $accession"
    fastqc "$file1" "$file2" --outdir="$output_dir"
done

# MultiQC
echo "Running MultiQC..."
multiqc ../outputs/fastqc/ -o ../outputs/multiqc --filename multiqc_non_trimmed.html

echo "=== $(date) ==="

