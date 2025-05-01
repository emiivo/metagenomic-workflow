#!/bin/bash


ACCOUNT_FILE="galaxy/account.txt"
LOG_DIR="../outputs/galaxy"
LOG_FILE="$LOG_DIR/ftp_upload.log"
DIR_TO_UPLOAD="../outputs/fastq_trimmed"
GALAXY_FTP_HOST="ftp.usegalaxy.eu"

mkdir -p "$LOG_DIR"

# Galaxy login email
if [[ ! -f "$ACCOUNT_FILE" ]]; then
  echo "[$(date)] ERROR: Galaxy account file not \
  found: $ACCOUNT_FILE" | tee -a "$LOG_FILE"
  exit 1
fi
GALAXY_USERNAME=$(<"$ACCOUNT_FILE")
GALAXY_USERNAME=$(echo "$GALAXY_USERNAME" | tr -d '[:space:]')

# Ask for Galaxy FTP password
read -s -p "Enter Galaxy FTP password for $GALAXY_USERNAME: " GALAXY_PASSWORD
echo ""

exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== $(date) ==="

# Upload Files
echo "[$(date)] Uploading files from '$DIR_TO_UPLOAD' to Galaxy FTP \
for user '$GALAXY_USERNAME'..." | tee -a "$LOG_FILE"

lftp -u "$GALAXY_USERNAME","$GALAXY_PASSWORD" $GALAXY_FTP_HOST <<EOF
lcd $DIR_TO_UPLOAD
mput *.fastq.gz
bye
EOF

if [[ $? -eq 0 ]]; then
  echo "[$(date)] Files uploaded successfully." | tee -a "$LOG_FILE"
else
  echo "[$(date)] ERROR: FTP upload failed." | tee -a "$LOG_FILE"
  exit 1
fi

echo "=== $(date) ==="
