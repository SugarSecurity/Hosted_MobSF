import pulumi, json
import pulumi_aws as aws

# Get Default VPC and Subnets
default_vpc = aws.ec2.get_vpc(default=True)
default_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

# Create an ECS cluster
cluster = aws.ecs.Cluster("mobSF-cluster",
    name="mobSF-cluster",
    tags={
        "Name": "mobSF-cluster",
    },
    settings=[aws.ecs.ClusterSettingArgs(
        name="containerInsights",
        value="enabled",
    )],
)

# Create a task definition for MobSF
mobSF_task_definition = aws.ecs.TaskDefinition("mobSF-task-definition",
    family="mobSF-task",
    container_definitions="""[
        {
            "name": "mobSF",
            "image": "opensecurity/mobile-security-framework-mobsf:latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000
                }
            ],
            "memory": 2048,
            "cpu": 1024
        }
    ]""",
    requires_compatibilities=["FARGATE"],  # Add this line
    network_mode="awsvpc",                # Add this line
    cpu="1024",                            # Add this line
    memory="2048",                        # Add this line
)

# Create a service for MobSF
mobSF_service = aws.ecs.Service("mobSF-service",
    cluster=cluster.id,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=mobSF_task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        security_groups=[aws.ec2.SecurityGroup("mobSF-security-group",
            vpc_id=default_vpc.id,
            tags={
                "Name": "mobSF-security-group",
            },
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=8000,
                    to_port=8000,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="tcp",
                    from_port=0,
                    to_port=65535,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
        ).id],
        subnets=default_subnets.ids,
    ),
    tags={
        "Name": "mobSF-service",
    },
)

#pulumi.export("mobSF_url", mobSF_service.load_balancers[0].dns_name)