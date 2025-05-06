# Metagenomic Workflow

This repository contains a complete pipeline for downloading, QC, assembling, and taxonomically analyzing metagenomic data using local resources and Galaxy Europe (https://usegalaxy.eu/).

Important: Clone this repository into an empty directory, as the workflow creates files outside the cloned folder.

## Clone the Repository

git clone https://github.com/emiivo/metagenomic-workflow

## Required Input Files

Before running the pipeline, add the following files:

1. download/accession.txt  
   - Add the Bioproject ID.

2. galaxy/account.txt  
   - Add your account name for https://usegalaxy.eu/

3. galaxy/key.txt  
   - Add your API key from https://usegalaxy.eu/

You will be asked for:

- Your Galaxy password during the upload_to_ftp step.
- The databases to use for taxonomy (Viral, Bacteria, Plasmid, Archaea).

## Running the Workflow

To run everything:

make

## Makefile Targets

### Full Workflow

- make  
  Runs the entire workflow from data download to taxonomy result.

### Galaxy Workflow Segments. Can be used if it is decided to turn off the command line while Galaxy is running, but keep in mind that the log files will not be complete.

- make process_in_galaxy  
  Runs everything after Galaxy upload: MEGAHIT assembly, Quast QC, Kraken taxonomy, Kraken translate, download and analyze taxonomy results.

- make after_assembly  
  Runs from assembly QC to taxonomy results.

- make after_assembly_qc  
  Runs only the taxonomy steps after assembly QC.

- make after_kraken  
  Runs Kraken translate and downloads the output and analyses it.

### Individual Steps

- make download_data  
  - Uses esearch and efetch to create download/sra_accessions.txt.  
  - Downloads .sra files with prefetch.  
  - Converts them to .fastq using fasterq-dump and zips them.  
  - Output: ../inputs/  
  - Log: download/

- make QC  
  - Runs FastQC and MultiQC on raw data.  
  - Outputs:  
    - ../outputs/fastqc  
    - ../outputs/multiqc/multiqc_non_trimmed.html  
  - Log: ../outputs/quality_control.log

- make trim  
  - Uses fastp to trim reads.  
  - Output: ../outputs/fastq_trimmed  
  - Log: ../outputs/fastq_trimmed/fastp.log

- make QC_after  
  - Runs FastQC and MultiQC on trimmed data.  
  - Outputs:  
    - ../outputs/fastqc_trimmed  
    - ../outputs/multiqc/multiqc_trimmed.html  
  - Log: ../outputs/fastqc_trimmed/quality_control.log

- make upload_to_ftp  
  - Uploads trimmed files to Galaxy FTP.  
  - Prompts for your Galaxy password.  
  - Log: ftp_upload.log

- make upload_to_galaxy  
  - Uploads files from FTP to Galaxy history.  
  - History is named after the Bioproject ID.  
  - Log: ../outputs/galaxy/upload_from_ftp.log

- make assemble  
  - Runs MEGAHIT for assembly.  
  - Log: ../outputs/galaxy/megahit_paired.log

- make assembly_qc  
  - Runs Quast for assembly quality control.  
  - Log: ../outputs/galaxy/quast_metagenomic.log

- make download_assembly_qc  
  - Downloads Quast results.  
  - Output: ../outputs/galaxy/quast_downloads  
  - Log: ../outputs/galaxy/quast_download.log

- make taxonomy_one  
  - Runs Kraken in Galaxy.  
  - Prompts for databases: Viral, Bacteria, Plasmid, Archaea.  
  - Log: ../outputs/galaxy/kraken_taxonomy.log

- make taxonomy_translate  
  - Runs Kraken-translate.  
  - Log: ../outputs/galaxy/kraken_translate.log

- make download_taxonomy  
  - Downloads translated Kraken results.  
  - Output: ../outputs/taxonomy/translated_kraken  
  - Log: ../outputs/galaxy/kraken_translate_download.log

- make taxonomy_result  
  - Computes top 10 organisms per database from Kraken output.  
  - Output: ../outputs/taxonomy/results  
  - Log: ../outputs/taxonomy/results/kraken_processing.log

