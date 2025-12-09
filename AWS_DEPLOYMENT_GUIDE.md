# AWS Elastic Beanstalk Deployment Guide

## Overview

This guide walks you through deploying the TCGA Co-Deletion Analysis application to AWS Elastic Beanstalk.

## Important: Data Directory Size

**The `data/processed/` directory is ~6.1GB with 2,797 files.**

This is too large for GitHub (100MB file size limit). You have two deployment options:

### Option 1: Use AWS S3 for Data Storage (RECOMMENDED)

1. Upload processed data to S3
2. Modify `data/processed_loader.py` to fetch from S3
3. Deploy lightweight application code via GitHub

### Option 2: Direct Upload to Elastic Beanstalk

1. Create deployment package with processed data included
2. Upload ZIP directly to Elastic Beanstalk (max 512MB compressed)
3. May need to split data or compress aggressively

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- EB CLI installed: `pip install awsebcli`
- Processed data generated locally (run `python batch_process.py`)

## Step 0: Prepare Your Repository ✓

Your repo now contains:

1. **requirements.txt** - All Python dependencies
2. **application.py** - AWS Elastic Beanstalk entry point
3. **app.py** - Main Dash application
4. **data/processed/** - Pre-computed analysis results (NOT in git due to size)

## Step 1: Initialize Elastic Beanstalk

```bash
# Navigate to project directory
cd /path/to/Cbioportal

# Initialize EB application
eb init -p python-3.11 tcga-codeletion-app --region us-east-1

# Follow prompts:
# - Select your region
# - Application name: tcga-codeletion-app
# - Python version: 3.11 (or your version)
# - SSH: Yes (recommended for troubleshooting)
```

## Step 2: Deploy Application (Option 1 - Without Data)

If using S3 for data storage:

```bash
# Create environment and deploy
eb create tcga-codeletion-env

# This will:
# - Create EC2 instance
# - Install dependencies from requirements.txt
# - Run application.py
```

## Step 2: Deploy Application (Option 2 - With Data)

If including data in deployment package:

```bash
# Create a deployment package
mkdir deploy
cp -r . deploy/
cd deploy
zip -r ../application.zip . -x "*.git*" -x "*.venv*" -x "*__pycache__*"

# Upload to Elastic Beanstalk
eb create tcga-codeletion-env --source application.zip
```

**Note**: Compression may reduce size from 6.1GB to ~2-3GB, but this may still exceed EB limits.

## Step 3: Using S3 for Data Storage (RECOMMENDED)

### 3.1: Upload Data to S3

```bash
# Create S3 bucket
aws s3 mb s3://tcga-codeletion-data --region us-east-1

# Upload processed data
aws s3 sync data/processed/ s3://tcga-codeletion-data/processed/

# Verify upload
aws s3 ls s3://tcga-codeletion-data/processed/ --recursive | wc -l
# Should show ~2,797 files
```

### 3.2: Modify Application to Use S3

Update `data/processed_loader.py`:

```python
import boto3
import os
from io import BytesIO

# Configuration
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET', 'tcga-codeletion-data')
S3_PREFIX = os.environ.get('S3_PREFIX', 'processed/')

def get_processed_dir(study_id=None):
    if USE_S3:
        # Return S3 path
        if study_id:
            return f"{S3_PREFIX}{study_id}/"
        return S3_PREFIX
    else:
        # Return local path
        module_dir = os.path.dirname(__file__)
        processed_dir = os.path.join(module_dir, "processed")
        if study_id:
            return os.path.join(processed_dir, study_id)
        return processed_dir

def load_from_s3(s3_path):
    """Load file from S3 bucket."""
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_path)
    return BytesIO(obj['Body'].read())

# Then update each load function to check USE_S3 and call load_from_s3()
```

### 3.3: Set Environment Variables

```bash
# Set environment variables for EB
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/

# Add boto3 to requirements.txt
echo "boto3" >> requirements.txt
```

### 3.4: Configure IAM Role

Your EB instance needs S3 read permissions:

1. Go to AWS Console → IAM → Roles
2. Find role: `aws-elasticbeanstalk-ec2-role`
3. Attach policy: `AmazonS3ReadOnlyAccess`

Or create custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::tcga-codeletion-data",
        "arn:aws:s3:::tcga-codeletion-data/*"
      ]
    }
  ]
}
```

## Step 4: Configure Application Settings

Create `.ebextensions/python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
  aws:elasticbeanstalk:container:python:
    WSGIPath: application:application
```

## Step 5: Deploy and Monitor

```bash
# Deploy application
eb deploy

# Open application in browser
eb open

# Monitor logs
eb logs

# Check health
eb health
```

## Step 6: Scaling Configuration

For large datasets and multiple users:

```bash
# Enable autoscaling
eb scale 2

# Or configure via console:
# - Min instances: 1
# - Max instances: 4
# - Trigger: CPU > 70% for 5 minutes
```

## Troubleshooting

### Issue: Application won't start

```bash
# Check logs
eb logs

# SSH into instance
eb ssh

# Check application logs
tail -f /var/log/eb-engine.log
tail -f /var/log/web.stdout.log
```

### Issue: Out of memory

- Increase instance type: `t2.micro` → `t2.medium`
- Configure via: `eb scale --instance-type t2.medium`

### Issue: Slow data loading

- Ensure S3 bucket is in same region as EB
- Consider caching frequently accessed files
- Use CloudFront CDN for static assets

## Cost Estimates

**Option 1: S3 + Small Instance**
- EC2 t2.small: ~$17/month
- S3 storage (6.1GB): ~$0.14/month
- Data transfer: ~$0.09/GB
- **Total**: ~$20-30/month

**Option 2: Large Instance with Local Data**
- EC2 t2.medium: ~$34/month
- No S3 costs
- **Total**: ~$35-40/month

## Production Checklist

- [ ] Processed data uploaded to S3 or included in deployment
- [ ] application.py tested locally
- [ ] requirements.txt includes all dependencies
- [ ] Environment variables configured
- [ ] IAM roles configured for S3 access
- [ ] SSL certificate configured (optional)
- [ ] Custom domain configured (optional)
- [ ] Monitoring and alerts set up
- [ ] Backup strategy for S3 data

## Local Testing with AWS Configuration

```bash
# Test application.py locally
python application.py

# Should run on http://0.0.0.0:5000
```

## Additional Resources

- [AWS Elastic Beanstalk Python Guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)
- [Deploying Dash Apps](https://dash.plotly.com/deployment)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

## Support

For issues specific to this application:
- GitHub: https://github.com/TrevorZandi/TCGA-Codeletion
- Check logs: `eb logs`
- Monitor health: `eb health --refresh`
