import os
from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_ecs as ecs,
)
from aws_cdk import (
    aws_elasticloadbalancingv2 as elbv2,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct
from dotenv import load_dotenv


class StreamlitStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables from .env file
        env_path = Path("../frontend/.env")  # Adjust path as needed
        load_dotenv(dotenv_path=env_path)

        # Create VPC with public and private subnets
        vpc = ec2.Vpc(
            self,
            "FactCheckVPC",
            max_azs=2,  # Use 2 AZs for ALB requirement
            nat_gateways=1,  # Single NAT gateway for cost optimization
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(
            self,
            "FactCheckCluster",
            vpc=vpc,
            cluster_name="fact-check-cluster",
        )

        # Create IAM role for ECS task
        task_role = iam.Role(
            self,
            "FactCheckTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="IAM role for Fact Check Assistant ECS task",
        )

        # Add Bedrock permissions to the task role
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:GetFoundationModel",
                    "bedrock:ListFoundationModels",
                ],
                resources=["*"],
            )
        )

        # Create IAM role for ECS task execution
        execution_role = iam.Role(
            self,
            "FactCheckExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
            description="IAM role for ECS task execution",
        )

        # Create CloudWatch log group
        log_group = logs.LogGroup(
            self,
            "FactCheckLogGroup",
            log_group_name="/ecs/fact-check-assistant",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create ECS Task Definition with Graviton2 (ARM64) architecture
        task_definition = ecs.FargateTaskDefinition(
            self,
            "FactCheckTaskDefinition",
            memory_limit_mib=2048,
            cpu=1024,
            task_role=task_role,
            execution_role=execution_role,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )

        # Add container to task definition
        container = task_definition.add_container(
            "FactCheckContainer",
            image=ecs.ContainerImage.from_asset("../frontend"),  # Build from Dockerfile
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="fact-check-assistant",
                log_group=log_group,
            ),
            environment={
                "LANGFUSE_SECRET_KEY": os.environ["LANGFUSE_SECRET_KEY"],
                "LANGFUSE_PUBLIC_KEY": os.environ["LANGFUSE_PUBLIC_KEY"],
                "LANGFUSE_HOST": os.environ["LANGFUSE_HOST"],
            },
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "curl -f http://localhost:8501/_stcore/health || exit 1",
                ],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )

        # Add port mapping
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8501,
                protocol=ecs.Protocol.TCP,
            )
        )

        # Create security group for ECS service
        ecs_security_group = ec2.SecurityGroup(
            self,
            "ECSSecurityGroup",
            vpc=vpc,
            description="Security group for ECS Fargate service",
            allow_all_outbound=True,
        )

        # Create security group for ALB
        alb_security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        # Allow HTTP traffic to ALB
        alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic from internet",
        )

        # Allow ALB to communicate with ECS service
        ecs_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(8501),
            description="Allow traffic from ALB to ECS service",
        )

        # Create Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "FactCheckALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        # Create ECS Service
        service = ecs.FargateService(
            self,
            "FactCheckService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            security_groups=[ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            assign_public_ip=False,
            service_name="fact-check-service",
        )

        # Create target group for the service
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "FactCheckTargetGroup",
            port=8501,
            protocol=elbv2.ApplicationProtocol.HTTP,
            vpc=vpc,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                healthy_http_codes="200",
                interval=Duration.seconds(30),
                path="/_stcore/health",
                protocol=elbv2.Protocol.HTTP,
                timeout=Duration.seconds(10),
                unhealthy_threshold_count=3,
            ),
        )

        # Add ECS service to target group
        service.attach_to_application_target_group(target_group)

        # Create ALB listener
        listener = alb.add_listener(
            "FactCheckListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[target_group],
        )

        # Configure auto-scaling
        scaling = service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=3,
        )

        # Scale based on CPU utilization
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )

        # Scale based on memory utilization
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )

        # Output the ALB DNS name
        CfnOutput(
            self,
            "LoadBalancerDNS",
            value=alb.load_balancer_dns_name,
            description="DNS name of the Application Load Balancer",
        )

        # Output the application URL
        CfnOutput(
            self,
            "ApplicationURL",
            value=f"http://{alb.load_balancer_dns_name}",
            description="URL to access the Fact Check Assistant application",
        )
