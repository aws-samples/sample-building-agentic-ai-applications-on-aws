#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.streamlit_stack import StreamlitStack

app = cdk.App()

# Get environment variables or use defaults
account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

env = cdk.Environment(account=account, region=region)

# Create the Streamlit stack
StreamlitStack(
    app,
    "FactCheckAssistantStack",
    env=env,
    description="Fact Check Assistant Streamlit App on ECS Fargate",
)

app.synth()
