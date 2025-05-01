#!/bin/bash

fastq_dir="../inputs"
trimmed_dir="../outputs/fastq_trimmed"
log_file="../outputs/fastq_trimmed/fastp.log"

# Log
mkdir -p "$(dirname "$log_file")"
echo "=== $(date) ===" > "$log_file"

# fastp
for fastq_file in "$fastq_dir"/*_1.fastq.gz; do
    base_name=$(basename "$fastq_file" _1.fastq.gz)
    file1="$fastq_dir/${base_name}_1.fastq.gz"
    file2="$fastq_dir/${base_name}_2.fastq.gz"
    out1="$trimmed_dir/${base_name}_1.fastq.gz"
    out2="$trimmed_dir/${base_name}_2.fastq.gz"
    json="$trimmed_dir/${base_name}.json"
    html="$trimmed_dir/${base_name}.html"

    echo "Processing: $file1 and $file2" | tee -a "$log_file"
    
    if [[ ! -f "$file1" || ! -f "$file2" ]]; then
        echo "Error: One or both input files not found: $file1, $file2" | tee -a "$log_file"
        continue
    fi

    fastp -i "$file1" -I "$file2" -o "$out1" -O "$out2" -j "$json" -h "$html" --verbose 2>&1 | tee -a "$log_file"
    
    if [ $? -eq 0 ]; then
        echo "Completed: $file1 and $file2" | tee -a "$log_file"
    else
        echo "Error processing: $file1 and $file2" | tee -a "$log_file"
    fi
done

echo "=== $(date) ===" >> "$log_file"

