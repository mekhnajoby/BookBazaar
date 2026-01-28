# AWS Deployment Guide for BookBazaar

This guide covers deploying BookBazaar to AWS using EC2, DynamoDB, SNS, and IAM.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   EC2       │───▶│  DynamoDB   │    │    SNS      │     │
│  │  (Flask)    │    │  (Database) │    │(Notifications)│   │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                     ▲             │
│         │           ┌─────────────┐          │             │
│         └──────────▶│    IAM      │──────────┘             │
│                     │  (Security) │                         │
│                     └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Step 1: EC2 Instance Setup

### 1.1 Launch EC2 Instance
1. Go to AWS Console → EC2 → Launch Instance
2. Choose **Amazon Linux 2023** or **Ubuntu 22.04 LTS**
3. Instance type: **t2.micro** (free tier) or **t2.small** for production
4. Create or select a key pair for SSH access

### 1.2 Configure Security Group
Create a security group with these inbound rules:

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | Your IP | Admin access |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom TCP | 5000 | 0.0.0.0/0 | Flask dev server (optional) |

### 1.3 Connect and Setup
```bash
# SSH into instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Update system
sudo yum update -y  # Amazon Linux
# or
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python and dependencies
sudo yum install python3 python3-pip git -y
# or
sudo apt install python3 python3-pip python3-venv git -y

# Clone your project
git clone <your-repo-url> BookBazaar
cd BookBazaar

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install production server
pip install gunicorn
```

### 1.4 Run with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 1.5 Setup as System Service
Create `/etc/systemd/system/bookbazaar.service`:
```ini
[Unit]
Description=BookBazaar Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/BookBazaar
Environment="PATH=/home/ec2-user/BookBazaar/venv/bin"
ExecStart=/home/ec2-user/BookBazaar/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bookbazaar
sudo systemctl start bookbazaar
```

## Step 2: DynamoDB Setup

### 2.1 Create DynamoDB Tables

**Users Table:**
- Table name: `bookbazaar-users`
- Partition key: `id` (Number)
- GSI: `email-index` with partition key `email`

**Books Table:**
- Table name: `bookbazaar-books`
- Partition key: `id` (Number)
- GSI: `category-index` with partition key `category_id`

**Orders Table:**
- Table name: `bookbazaar-orders`
- Partition key: `id` (Number)
- GSI: `user-index` with partition key `user_id`

### 2.2 Update Application Code
Install boto3:
```bash
pip install boto3
```

Example DynamoDB connection:
```python
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('bookbazaar-users')
```

## Step 3: AWS SNS Setup

### 3.1 Create SNS Topic
1. Go to AWS Console → SNS → Topics
2. Create topic: `bookbazaar-notifications`
3. Note the ARN

### 3.2 Create Subscriptions
- Add email subscriptions for order notifications
- Add SMS subscriptions for urgent alerts

### 3.3 Update Application Code
```python
import boto3

sns = boto3.client('sns', region_name='us-east-1')

def send_notification(message, subject):
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:ACCOUNT:bookbazaar-notifications',
        Message=message,
        Subject=subject
    )
```

## Step 4: IAM Configuration

### 4.1 Create IAM Role for EC2
Create role: `bookbazaar-ec2-role` with policies:
- `AmazonDynamoDBFullAccess`
- `AmazonSNSFullAccess`

### 4.2 Attach Role to EC2
1. Go to EC2 → Instance → Actions → Security → Modify IAM Role
2. Select `bookbazaar-ec2-role`

### 4.3 Create IAM Users (Optional)
For admin access:
- Create user with programmatic access
- Attach appropriate policies
- Store credentials securely

## Step 5: Environment Variables

Create `.env` on EC2:
```bash
SECRET_KEY=your-production-secret-key
AWS_REGION=us-east-1
DYNAMODB_USERS_TABLE=bookbazaar-users
DYNAMODB_BOOKS_TABLE=bookbazaar-books
DYNAMODB_ORDERS_TABLE=bookbazaar-orders
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:ACCOUNT:bookbazaar-notifications
```

## Step 6: Domain & SSL (Optional)

### Using Nginx as Reverse Proxy
```bash
sudo yum install nginx -y
```

Configure `/etc/nginx/conf.d/bookbazaar.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Add SSL with Certbot
```bash
sudo yum install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

## Quick Deployment Checklist

- [ ] Launch EC2 instance
- [ ] Configure security groups
- [ ] Install Python and dependencies
- [ ] Clone application code
- [ ] Create DynamoDB tables
- [ ] Create SNS topic
- [ ] Configure IAM role
- [ ] Set environment variables
- [ ] Start application with Gunicorn
- [ ] (Optional) Setup Nginx and SSL

## Monitoring & Maintenance

- Use **CloudWatch** for logs and metrics
- Set up **alarms** for high CPU/memory usage
- Enable **DynamoDB auto-scaling** for traffic spikes
- Regular **backups** of DynamoDB tables
