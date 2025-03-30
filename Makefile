# Makefile

# Define the script and files
DOWNLOAD_SCRIPT = download/download.sh
INPUTS_DIR = inputs
SRA_ACCESSION_FILE = download/sra_accessions.txt
ACCESSION_FILE = download/accession.txt

# Default target to run the download script
all: download_data

# Download data target
download_data:
	# Ensure the script is executable
	chmod +x $(DOWNLOAD_SCRIPT)
	# Run the download script in the correct directory
	cd download && ./download.sh

# Clean target to remove downloaded files
clean:
	rm -rf $(INPUTS_DIR)/*
	rm -f $(SRA_ACCESSION_FILE)

# Distclean target to remove everything including the download.sh file
distclean: clean
	rm -f $(DOWNLOAD_SCRIPT)

