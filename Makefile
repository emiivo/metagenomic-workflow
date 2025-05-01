# Makefile

# Define the script and files
INPUTS_DIR = ../inputs
OUTPUTS_DIR = ../outputs 
SRA_ACCESSION_FILE = download/sra_accessions.txt
ACCESSION_FILE = download/accession.txt
DOWNLOAD_SCRIPT = download/download.sh
QC_SCRIPT = quality_control.sh
TRIM_SCRIPT = trimming.sh
QC_AFTER_SCRIPT = quality_after_trim.sh
UPLOAD_FTP_SCRIPT = upload_to_ftp.sh
UPLOAD_GALAXY_SCRIPT = upload_to_galaxy.py
ASSEMBLY_SCRIPT = assembly.py
ASSEMBLY_QC_SCRIPT = assembly_qc.py
DOWNLOAD_ASSEMBLY_QC = download_assembly_qc.py
TAXONOMY_STEP_ONE = taxonomy_step_one.py
TAXONOMY_STEP_TWO = taxonomy_translate.py
TAXONOMY_DOWNLOAD = download_taxonomy.py

# Default target to run the entire workflow
all: download_data QC trim upload_to_ftp upload_to_galaxy \
     assemble assembly_qc download_assembly_qc taxonomy_one \
     taxonomy_translate taxonomy_download
     
# Target to run the workflow after galaxy upload - assembly,
# assembly qc, taxonomy
process_in_galaxy: assemble assembly_qc download_assembly_qc taxonomy_one \
     taxonomy_translate taxonomy_download
     
# Target to run the workflow after assembly -
# assembly qc, taxonomy 
after_assembly: assembly_qc download_assembly_qc taxonomy_one \
     taxonomy_translate taxonomy_download  

# Target to run the workflow after assembly qc - taxonomy    
after_assembly_qc: download_assembly_qc taxonomy_one \
     taxonomy_translate taxonomy_download  
     
# Target to run the workflow after running kraken - translate 
# and download  
after_assembly_qc: taxonomy_translate taxonomy_download

# Download data target
download_data:
	chmod +x $(DOWNLOAD_SCRIPT)
	cd download && ./$(DOWNLOAD_SCRIPT)
	
QC:
	chmod +x $(QC_SCRIPT)
	./$(QC_SCRIPT)
	
trim:
	chmod +x $(TRIM_SCRIPT)
	./$(TRIM_SCRIPT)
	
QC_after:
	chmod +x $(QC_AFTER_SCRIPT)
	./$(QC_AFTER_SCRIPT)	
	
upload_to_ftp:
	chmod +x $(UPLOAD_FTP_SCRIPT)
	./$(UPLOAD_FTP_SCRIPT)	

upload_to_galaxy:
	chmod +x $(UPLOAD_GALAXY_SCRIPT)
	./$(UPLOAD_GALAXY_SCRIPT)
	
assemble:
	chmod +x $(ASSEMBLY_SCRIPT)
	./$(ASSEMBLY_SCRIPT)		

assembly_qc:
	chmod +x $(ASSEMBLY_QC_SCRIPT)
	./$(ASSEMBLY_QC_SCRIPT)
	
download_assembly_qc:
	chmod +x $(DOWNLOAD_ASSEMBLY_QC)
	./$(DOWNLOAD_ASSEMBLY_QC)	

taxonomy_one:
	chmod +x $(TAXONOMY_STEP_ONE)
	./$(TAXONOMY_STEP_ONE)
	
taxonomy_translate:
	chmod +x $(TAXONOMY_STEP_TWO)
	./$(TAXONOMY_STEP_TWO)	
	
taxonomy_download:
	chmod +x $(TAXONOMY_DOWNLOAD)
	./$(TAXONOMY_DOWNLOAD)	

# Clean target to remove downloaded files
clean:
	rm -rf $(INPUTS_DIR)/*
	rm -rf $(OUTPUTS_DIR)/*
	rm -f $(SRA_ACCESSION_FILE)

# Distclean target to remove everything
distclean: clean
	rm -f $(DOWNLOAD_SCRIPT)
	rm -f $(QC_SCRIPT)
	rm -f $(TRIM_SCRIPT)	
	rm -f $(QC_AFTER_SCRIPT)
	rm -f $(UPLOAD_FTP_SCRIPT)		
	rm -f $(UPLOAD_GALAXY_SCRIPT)	
	rm -f $(ASSEMBLY_SCRIPT)	
