# AWS Deployment Quick Start

Your application is now ready for AWS Elastic Beanstalk deployment with S3 data storage!

## ✅ Pre-Deployment Checklist

- [x] S3 integration implemented in `data/processed_loader.py`
- [x] Data uploaded to S3 bucket `tcga-codeletion-data`
- [x] `application.py` created for EB
- [x] `requirements.txt` includes boto3
- [x] `.ebextensions/01_python.config` configured
- [x] S3 connectivity tested successfully

## 🚀 Deployment Steps

### 1. Install EB CLI (if not already installed)

```bash
pip install awsebcli
```

### 2. Initialize Elastic Beanstalk

```bash
cd /path/to/Cbioportal

# Initialize EB application
eb init -p python-3.12 tcga-codeletion-app --region us-east-1

# When prompted:
# - Application name: tcga-codeletion-app
# - Python version: 3.12
# - Set up SSH: Yes (recommended)
```

### 3. Create Environment with S3 Configuration

```bash
# Create environment
eb create tcga-codeletion-env

# Wait for environment to be created (5-10 minutes)
# Then set environment variables for S3
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/
```

### 4. Configure IAM Role for S3 Access

The EB instance needs permission to read from S3:

**Option A: Via AWS Console**
1. Go to AWS Console → IAM → Roles
2. Find role: `aws-elasticbeanstalk-ec2-role`
3. Click "Attach policies"
4. Search for and attach: `AmazonS3ReadOnlyAccess`

**Option B: Via AWS CLI**
```bash
# Get the instance profile
aws elasticbeanstalk describe-configuration-settings \
  --application-name tcga-codeletion-app \
  --environment-name tcga-codeletion-env \
  --query "ConfigurationSettings[0].OptionSettings[?Namespace=='aws:autoscaling:launchconfiguration' && OptionName=='IamInstanceProfile'].Value" \
  --output text

# Attach S3 read policy to the role
aws iam attach-role-policy \
  --role-name aws-elasticbeanstalk-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### 5. Deploy and Open

```bash
# Deploy your application
eb deploy

# Open in browser
eb open
```

## 🧪 Testing Deployment

### Check Application Health
```bash
eb health
```

### View Logs
```bash
eb logs
```

### SSH into Instance (if needed)
```bash
eb ssh
```

## 📊 Monitoring

### View Application Logs
```bash
# Recent logs
eb logs --stream

# Download all logs
eb logs --all
```

### Check S3 Data Access
```bash
# SSH into instance
eb ssh

# Test S3 access
cd /var/app/current
python test_s3_connection.py
```

## 🔧 Troubleshooting

### Application Won't Start
```bash
# Check logs for errors
eb logs

# Common issues:
# 1. Missing IAM permissions for S3
# 2. Wrong environment variables
# 3. Python version mismatch
```

### Slow Loading Times
- Ensure S3 bucket is in same region as EB (us-east-1)
- Consider enabling CloudFront CDN
- Increase instance size if needed

### Out of Memory
```bash
# Scale to larger instance
eb scale --instance-type t2.medium

# Or add more instances
eb scale 2
```

## 💰 Cost Estimates

**Recommended Setup:**
- Instance: t2.small (~$17/month)
- S3 Storage: 6.1GB (~$0.14/month)
- Data Transfer: Minimal (~$1-2/month)
- **Total: ~$20-25/month**

## 🔄 Updating Application

```bash
# Make changes to code
git add .
git commit -m "Update description"
git push

# Deploy updates
eb deploy
```

## 🛑 Terminating Environment (when done)

```bash
# Terminate environment (stops charges)
eb terminate tcga-codeletion-env

# Data in S3 remains intact
```

## 📚 Additional Commands

```bash
# List all environments
eb list

# Check environment status
eb status

# Open AWS console
eb console

# View current configuration
eb config

# Set environment variables
eb setenv KEY=value

# Print environment variables
eb printenv
```

## ✅ Verification Steps

After deployment, verify:

1. **Application loads**: Navigate to EB URL
2. **Homepage displays**: Check navigation cards work
3. **Co-deletion explorer**: Select study and chromosome, verify heatmap loads
4. **Summary statistics**: Check deletion frequency distribution displays
5. **Data from S3**: Confirm 31 studies are available in dropdown

## 🆘 Support

- **AWS EB Docs**: https://docs.aws.amazon.com/elasticbeanstalk/
- **Dash Deployment**: https://dash.plotly.com/deployment
- **GitHub Issues**: https://github.com/TrevorZandi/TCGA-Codeletion/issues

---

**Ready to deploy!** Run `eb init` to get started. 🎉
