# AWS Elastic Beanstalk Deployment Guide

Complete guide for deploying the TCGA Co-Deletion Analysis application to AWS Elastic Beanstalk with S3 data storage.

## Architecture

The application uses **AWS S3 for data storage** (~6.1GB of processed data) and Elastic Beanstalk for the web application. The application code automatically loads data from S3 when the `USE_S3` environment variable is set to `true`.

## Prerequisites

✅ **Ready for Deployment:**
- [x] AWS Account with credentials configured
- [x] AWS CLI installed and configured (`aws configure`)
- [x] Processed data uploaded to S3 bucket
- [x] S3 integration implemented in application
- [x] Application tested with S3 (`python test_s3_connection.py`)

**Install EB CLI:**
```bash
pip install awsebcli
```

## Step 1: Initialize Elastic Beanstalk

```bash
cd /path/to/Cbioportal

# Initialize EB application
eb init -p python-3.12 tcga-codeletion-app --region us-east-1

# When prompted:
# - Application name: tcga-codeletion-app
# - Python version: 3.12
# - Set up SSH: Yes (recommended)
```

## Step 2: Create Environment

```bash
# Create environment (takes 5-10 minutes)
eb create tcga-codeletion-env

# Wait for "Environment health has transitioned to Ok"
```

## Step 3: Configure Environment Variables

```bash
# Set S3 configuration
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/
```

## Step 4: Configure IAM Role for S3 Access

**Option A: Via AWS Console (Easiest)**
1. Go to AWS Console → IAM → Roles
2. Find role: `aws-elasticbeanstalk-ec2-role`
3. Click "Attach policies"
4. Search for and attach: `AmazonS3ReadOnlyAccess`

**Option B: Via AWS CLI**
```bash
aws iam attach-role-policy \
  --role-name aws-elasticbeanstalk-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

## Step 5: Deploy and Verify

```bash
# Deploy application
eb deploy

# Open in browser
eb open

# Check application health
eb health
```

## Verification

After deployment, test your application:

1. **Homepage loads** - Verify navigation works
2. **Co-deletion Explorer** - Select study/chromosome, check heatmap displays
3. **Summary Statistics** - Verify deletion frequency chart loads
4. **31 studies available** - Confirm all studies appear in dropdown

### View Logs
```bash
# Stream logs in real-time
eb logs --stream

# Download all logs
eb logs
```

### SSH Into Instance
```bash
eb ssh

# Once connected, test S3 access
cd /var/app/current
python test_s3_connection.py
```

## Scaling (Optional)

```bash
# Scale to multiple instances
eb scale 2

# Or increase instance size
eb scale --instance-type t2.medium
```

## Troubleshooting

### Application Won't Start
```bash
eb logs              # Check for errors
eb ssh               # SSH into instance
tail -f /var/log/eb-engine.log
```

**Common Issues:**
- Missing IAM permissions for S3 → Attach `AmazonS3ReadOnlyAccess` policy
- Wrong environment variables → Check with `eb printenv`
- Python version mismatch → Verify in `.ebextensions/01_python.config`

### Slow Loading
- Ensure S3 bucket and EB are in same region (us-east-1)
- Increase instance size: `eb scale --instance-type t2.medium`

### Out of Memory
- Scale up: `eb scale --instance-type t2.medium`
- Add instances: `eb scale 2`

## Management Commands

```bash
# Update application
git push                 # Push changes
eb deploy                # Deploy updates

# Monitor
eb health                # Check status
eb logs                  # View logs
eb printenv              # Show environment variables

# Manage environment
eb list                  # List environments
eb status                # Environment details
eb console               # Open AWS console
eb terminate             # Delete environment (stops charges)
```

## Cost Estimates

**Recommended Setup (t2.small):**
- EC2 instance: ~$17/month
- S3 storage (6.1GB): ~$0.14/month
- Data transfer: ~$1-2/month
- **Total: ~$20-25/month**

**Larger Setup (t2.medium):**
- EC2 instance: ~$34/month
- **Total: ~$35-40/month**

## Quick Reference

### Initial Deployment
```bash
eb init -p python-3.12 tcga-codeletion-app --region us-east-1
eb create tcga-codeletion-env
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/
# Configure IAM role via AWS Console
eb deploy
eb open
```

### Update Application
```bash
git add .
git commit -m "Update"
git push
eb deploy
```

### Stop Charges
```bash
eb terminate tcga-codeletion-env
```

## Resources

- **AWS EB Docs**: https://docs.aws.amazon.com/elasticbeanstalk/
- **GitHub**: https://github.com/TrevorZandi/TCGA-Codeletion
- **Dash Deployment**: https://dash.plotly.com/deployment
