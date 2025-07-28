#!/bin/bash

# Fact Check Assistant - CDK Deployment Script
# This script will deploy the Streamlit app with all environment variables configured

set -e  # Exit on any error

echo "🚀 Starting Fact Check Assistant deployment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Installing..."
    npm install -g aws-cdk
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Check for required files
echo "📋 Checking for required files..."

# Define the required files
REQUIRED_FILES=(
  "../frontend/math_assistant.py"
  "../frontend/research_assistant.py"
  "../frontend/claim_detection_assistant.py"
  "../frontend/fact_check_supervisor.py"
)

# Check each file
for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Required file not found: $file"
    echo "   Please ensure all required files are present before deploying."
    exit 1
  fi
done

echo "✅ All required files found"

# Install Python dependencies
echo "📦 Installing CDK dependencies..."
pip install aws-cdk-lib==2.89.0 constructs==10.4.2

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-west-2"
    echo "⚠️  No default region set, using us-west-2"
fi

echo "🔧 Deploying to Account: $AWS_ACCOUNT, Region: $AWS_REGION"

# Set CDK environment variables
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
export CDK_DEFAULT_REGION=$AWS_REGION

# Bootstrap CDK (if not already done)
echo "🏗️  Bootstrapping CDK (if needed)..."
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION

# Synthesize the stack (optional but good for verification)
echo "🔍 Synthesizing CloudFormation template..."
cdk synth

# Deploy the stack
echo "🚀 Deploying the stack..."
echo "This may take 10-15 minutes as it builds the Docker image and creates AWS resources..."

cdk deploy --require-approval never

# Get the outputs
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Stack Outputs:"
cdk list --long 2>/dev/null || true

# Try to get the application URL
APP_URL=$(aws cloudformation describe-stacks \
    --stack-name FactCheckAssistantStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [ ! -z "$APP_URL" ]; then
    echo ""
    echo "🌐 Your Fact Check Assistant is available at:"
    echo "   $APP_URL"
    echo ""
    echo "⏰ Note: It may take 2-3 minutes for the health checks to pass"
    echo "   and the application to become fully available."
else
    echo ""
    echo "📝 To get your application URL, run:"
    echo "   aws cloudformation describe-stacks --stack-name FactCheckAssistantStack --query 'Stacks[0].Outputs'"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: aws logs tail /ecs/fact-check-assistant --follow"
echo "   Destroy stack: cdk destroy"
echo "   Update stack: ./deploy.sh"
