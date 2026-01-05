#!/bin/bash
#
# Upload processed data to AWS S3 for Elastic Beanstalk deployment
#
# Usage:
#   ./upload_data_to_s3.sh [bucket-name]
#
# Example:
#   ./upload_data_to_s3.sh tcga-codeletion-data
#

cd "$(dirname "$0")/.."

set -e

BUCKET_NAME=${1:-tcga-codeletion-data}
REGION=${2:-us-east-1}
DATA_DIR="data/processed"

echo "======================================"
echo "TCGA Co-Deletion Data Upload to S3"
echo "======================================"
echo ""
echo "Bucket: s3://${BUCKET_NAME}"
echo "Region: ${REGION}"
echo "Source: ${DATA_DIR}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "Install: pip install awscli"
    exit 1
fi

# Check if data directory exists
if [ ! -d "${DATA_DIR}" ]; then
    echo "❌ Error: ${DATA_DIR} directory not found"
    echo "Run: python batch_process.py"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

echo "✓ AWS CLI configured"
echo "✓ Data directory found"
echo ""

# Count files
FILE_COUNT=$(find ${DATA_DIR} -type f | wc -l)
echo "📊 Found ${FILE_COUNT} files to upload"
echo ""

# Prompt for confirmation
read -p "Continue with upload? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upload cancelled"
    exit 0
fi

# Create bucket if it doesn't exist
echo "📦 Checking if bucket exists..."
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "✓ Bucket exists"
else
    echo "Creating bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"
    echo "✓ Bucket created"
fi
echo ""

# Upload data with progress
echo "⬆️  Uploading data to S3..."
echo "This may take 30-60 minutes depending on your connection speed"
echo ""

aws s3 sync "${DATA_DIR}/" "s3://${BUCKET_NAME}/processed/" \
    --region "${REGION}" \
    --exclude "*.html" \
    --exclude "*_deletion_*.xlsx" \
    --exclude "*_codeletion_counts.xlsx" \
    --exclude "*_codeletion_matrix.xlsx"

echo ""
echo "✅ Upload complete!"
echo ""

# Verify upload
echo "🔍 Verifying upload..."
UPLOADED_COUNT=$(aws s3 ls "s3://${BUCKET_NAME}/processed/" --recursive | wc -l)
echo "✓ Found ${UPLOADED_COUNT} files in S3"
echo ""

# Calculate size
BUCKET_SIZE=$(aws s3 ls "s3://${BUCKET_NAME}/processed/" --recursive --summarize | grep "Total Size" | awk '{print $3}')
BUCKET_SIZE_MB=$((BUCKET_SIZE / 1024 / 1024))
echo "✓ Total size: ${BUCKET_SIZE_MB} MB"
echo ""

echo "======================================"
echo "Next Steps:"
echo "======================================"
echo ""
echo "1. Update your Elastic Beanstalk environment variables:"
echo "   eb setenv USE_S3=true S3_BUCKET=${BUCKET_NAME} S3_PREFIX=processed/"
echo ""
echo "2. Ensure boto3 is in requirements.txt:"
echo "   echo 'boto3' >> requirements.txt"
echo ""
echo "3. Configure IAM role for S3 access"
echo "   See AWS_DEPLOYMENT_GUIDE.md for details"
echo ""
echo "4. Deploy your application:"
echo "   eb deploy"
echo ""
