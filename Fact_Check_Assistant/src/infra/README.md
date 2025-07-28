# Fact Check Assistant - AWS CDK Deployment

This directory contains the AWS CDK infrastructure code to deploy the Fact Check Assistant Streamlit application on ECS Fargate with a secure architecture.

## Architecture Overview

The deployment creates:
- **VPC**: Custom VPC with public and private subnets across 2 AZs
- **Application Load Balancer**: Internet-facing ALB in public subnets
- **ECS Fargate Service**: Containerized Streamlit app running in private subnets
- **Security Groups**: Restrictive security groups allowing only necessary traffic
- **Auto Scaling**: CPU and memory-based auto scaling (1-3 tasks)

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **AWS CDK installed**: `npm install -g aws-cdk`
3. **Python 3.8+** installed
4. **Docker** installed and running

## Deployment Steps

### 1. Install Dependencies

```bash
cd Fact_Check_Assistant/src/infra
pip install -r requirements.txt
```

### 2. Bootstrap CDK (First time only)

```bash
cdk bootstrap
```

### 3. Deploy the Stack

```bash
# Synthesize CloudFormation template (optional - for review)
cdk synth

# Deploy the stack
cdk deploy
```

### 4. Access the Application

After deployment completes, the CDK will output:
- `LoadBalancerDNS`: The DNS name of the Application Load Balancer
- `ApplicationURL`: The complete URL to access your application

Example output:
```
Outputs:
FactCheckAssistantStack.LoadBalancerDNS = FactCheckAssistantStack-FactCheckALB-1234567890.us-east-1.elb.amazonaws.com
FactCheckAssistantStack.ApplicationURL = http://FactCheckAssistantStack-FactCheckALB-1234567890.us-east-1.elb.amazonaws.com
```

## Environment Variables

The application uses the following environment variables (configured in the CDK stack):
- `LANGFUSE_SECRET_KEY`: Langfuse secret key for observability
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key for observability  
- `LANGFUSE_HOST`: Langfuse host URL

## Security Features

- **Private Subnets**: Application runs in private subnets with no direct internet access
- **Security Groups**: Restrictive rules allowing only ALB → ECS communication
- **NAT Gateway**: Outbound internet access for package downloads and API calls
- **Health Checks**: Application and load balancer health monitoring

## Monitoring and Logs

- **CloudWatch Logs**: Application logs are sent to `/ecs/fact-check-assistant`
- **Health Checks**: Both ECS and ALB health checks configured
- **Auto Scaling**: Scales based on CPU (70%) and Memory (80%) utilization

## Cost Optimization

- **Single NAT Gateway**: Reduces NAT gateway costs
- **Fargate**: Pay-per-use compute without managing EC2 instances
- **Log Retention**: CloudWatch logs retained for 1 week only

## Cleanup

To avoid ongoing charges, destroy the stack when no longer needed:

```bash
cdk destroy
```

## Troubleshooting

### Common Issues

1. **Docker Build Fails**
   - Ensure Docker is running
   - Check that all files exist in the frontend directory

2. **Deployment Fails**
   - Verify AWS credentials are configured
   - Check that CDK is bootstrapped in your account/region

3. **Application Not Accessible**
   - Wait 2-3 minutes after deployment for health checks to pass
   - Check ECS service status in AWS Console

4. **Health Check Failures**
   - Verify Streamlit is running on port 8501
   - Check CloudWatch logs for application errors

### Useful Commands

```bash
# View stack status
cdk list

# View differences before deployment
cdk diff

# View CloudFormation template
cdk synth

# Deploy with verbose output
cdk deploy --verbose
```

## Customization

### Scaling Configuration

To modify auto-scaling parameters, edit `streamlit_stack.py`:

```python
# Change min/max capacity
scaling = service.auto_scale_task_count(
    min_capacity=2,  # Increase minimum
    max_capacity=5,  # Increase maximum
)

# Adjust scaling thresholds
scaling.scale_on_cpu_utilization(
    "CpuScaling",
    target_utilization_percent=60,  # Scale at lower CPU
)
```

### Resource Allocation

To modify CPU/memory allocation:

```python
task_definition = ecs.FargateTaskDefinition(
    self,
    "FactCheckTaskDefinition",
    memory_limit_mib=4096,  # Increase memory
    cpu=2048,               # Increase CPU
    # ...
)
```

### Environment Variables

To add or modify environment variables, update the container definition:

```python
environment={
    "LANGFUSE_SECRET_KEY": "your-secret-key",
    "LANGFUSE_PUBLIC_KEY": "your-public-key", 
    "LANGFUSE_HOST": "https://cloud.langfuse.com",
    "NEW_VARIABLE": "new-value",
},
```

## Support

For issues with the CDK deployment, check:
1. AWS CDK documentation: https://docs.aws.amazon.com/cdk/
2. ECS Fargate documentation: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
3. Application Load Balancer documentation: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/
