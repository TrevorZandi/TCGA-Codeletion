# AWS Deployment Checklist

Use this checklist when deploying to AWS Elastic Beanstalk.

## Pre-Deployment Checklist

- [ ] **Processed data generated locally**
  ```bash
  python src/batch_process.py
  # Verify: ls -lh data/processed/
  ```

- [ ] **AWS CLI installed and configured**
  ```bash
  pip install awscli
  aws configure
  # Enter: Access Key, Secret Key, Region (us-east-1), Output format (json)
  ```

- [ ] **EB CLI installed**
  ```bash
  pip install awsebcli
  eb --version
  ```

- [ ] **Application tested locally**
  ```bash
  python src/application.py
  # Visit: http://localhost:5000
  ```

## Step 1: Upload Data to S3

- [ ] **Create S3 bucket and upload data**
  ```bash
  ./scripts/upload_data_to_s3.sh tcga-codeletion-data us-east-1
  ```

- [ ] **Verify upload completed**
  ```bash
  aws s3 ls s3://tcga-codeletion-data/processed/ --recursive | wc -l
  # Should show ~2000-3000 files
  ```

## Step 2: Initialize Elastic Beanstalk

- [ ] **Initialize EB application**
  ```bash
  eb init -p python-3.11 tcga-codeletion-app --region us-east-1
  ```

- [ ] **Review generated files**
  ```bash
  cat .elasticbeanstalk/config.yml
  ```

## Step 3: Configure IAM for S3 Access

- [ ] **Option A: Use AWS Console**
  1. Go to IAM → Roles
  2. Find: `aws-elasticbeanstalk-ec2-role`
  3. Attach policy: `AmazonS3ReadOnlyAccess`

- [ ] **Option B: Use AWS CLI**
  ```bash
  aws iam attach-role-policy \
    --role-name aws-elasticbeanstalk-ec2-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
  ```

## Step 4: Create and Configure Environment

- [ ] **Create EB environment**
  ```bash
  eb create tcga-codeletion-env \
    --instance-type t2.small \
    --region us-east-1
  ```

- [ ] **Set environment variables for S3**
  ```bash
  eb setenv \
    USE_S3=true \
    S3_BUCKET=tcga-codeletion-data \
    S3_PREFIX=processed/
  ```

- [ ] **Add boto3 to requirements if using S3**
  ```bash
  echo "boto3" >> requirements.txt
  git add requirements.txt
  git commit -m "Add boto3 for S3 access"
  ```

## Step 5: Deploy Application

- [ ] **Deploy to EB**
  ```bash
  eb deploy
  ```

- [ ] **Monitor deployment**
  ```bash
  eb health --refresh
  ```

- [ ] **Check logs if issues occur**
  ```bash
  eb logs
  ```

## Step 6: Verify Deployment

- [ ] **Open application in browser**
  ```bash
  eb open
  ```

- [ ] **Test application functionality**
  - [ ] Homepage loads
  - [ ] Navigate to Co-Deletion Explorer
  - [ ] Select a study and chromosome
  - [ ] Verify heatmap displays
  - [ ] Navigate to Summary Statistics
  - [ ] Verify deletion frequency chart loads

- [ ] **Check application logs**
  ```bash
  eb logs --all
  ```

## Post-Deployment Configuration

- [ ] **Configure custom domain (optional)**
  ```bash
  # In AWS Console: EB → Environment → Configuration → Load Balancer
  # Add SSL certificate and CNAME record
  ```

- [ ] **Set up monitoring and alerts**
  - [ ] CloudWatch alarms for CPU, memory, errors
  - [ ] SNS notifications for health status changes

- [ ] **Configure autoscaling (optional)**
  ```bash
  eb scale 2  # Set to 2 instances
  # Or configure in console with triggers
  ```

## Troubleshooting Checklist

If deployment fails:

- [ ] **Check application logs**
  ```bash
  eb logs --all | grep -i error
  ```

- [ ] **SSH into instance**
  ```bash
  eb ssh
  tail -f /var/log/eb-engine.log
  tail -f /var/log/web.stdout.log
  ```

- [ ] **Verify S3 access**
  ```bash
  eb ssh
  aws s3 ls s3://tcga-codeletion-data/processed/ --recursive | head -10
  ```

- [ ] **Check IAM role permissions**
  - Instance profile has S3 read access
  - Trust relationship configured correctly

- [ ] **Verify environment variables**
  ```bash
  eb printenv
  ```

## Cleanup (if needed)

- [ ] **Terminate environment**
  ```bash
  eb terminate tcga-codeletion-env
  ```

- [ ] **Delete S3 bucket**
  ```bash
  aws s3 rb s3://tcga-codeletion-data --force
  ```

- [ ] **Remove EB application**
  ```bash
  eb terminate --all
  ```

## Estimated Timeline

- Data upload to S3: 30-60 minutes (depending on connection)
- EB environment creation: 5-10 minutes
- Application deployment: 3-5 minutes
- Total: ~45-75 minutes

## Estimated Costs

**Monthly Costs (S3 + t2.small instance):**
- EC2 t2.small: ~$17/month (730 hours)
- S3 storage (6.1GB): ~$0.14/month
- S3 requests: ~$0.01/month
- Data transfer: ~$0.09/GB
- **Total: ~$20-30/month**

**To reduce costs:**
- Use t2.micro instead: ~$9/month (free tier eligible)
- Stop instance when not in use
- Use spot instances (not recommended for production)

## Resources

- Full deployment guide: [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md)
- AWS EB Python docs: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html
- GitHub repo: https://github.com/TrevorZandi/TCGA-Codeletion

## Notes

Date deployed: _______________
Environment URL: _______________
S3 bucket name: _______________
AWS region: _______________
Instance type: _______________
