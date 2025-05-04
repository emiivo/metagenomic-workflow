#!/bin/bash

# Output directories
OUTPUT_DIR="../outputs/taxonomy/translated_kraken"
RESULTS_DIR="../outputs/taxonomy/results"
LOG_FILE="../outputs/taxonomy/results/kraken_processing.log"
TOP_N=10

# Log function
log_message() {
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "$timestamp $1" | tee -a "$LOG_FILE"
}

log_message "Starting Kraken dataset processing..."

for db_dir in "$OUTPUT_DIR"/*/; do
    db_name=$(basename "$db_dir")
    log_message "Processing Kraken database: $db_name"

    # Results directory
    db_results_dir="$RESULTS_DIR/$db_name"
    mkdir -p "$db_results_dir"
    log_message "Created directory"

    # Combine counts
    combined_counts_file="$db_results_dir/combined_counts.txt"
    > "$combined_counts_file"

    # Process files
    for tabular_file in "$db_dir"/*.tabular; do
        log_message "Processing file"

        # Check file existence
        if [ ! -f "$tabular_file" ]; then
            log_message "ERROR"
            continue
        fi

        # Append counts
        cut -f2,3 "$tabular_file" | sort | uniq -c >> "$combined_counts_file"
        log_message "Counts added"
    done

    # Top N taxa
    log_message "Calculating top N"
    sort "$combined_counts_file" | uniq -c | sort -nr | head -n "$TOP_N" > "$db_results_dir/top_${db_name}_taxa.txt"
    log_message "Top N taxa written"

done

log_message "All Kraken datasets processed!"

