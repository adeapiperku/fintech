# Terraform Deployment for Fintech Fraud Agent

This Terraform stack deploys the fraud agent pipeline as a scheduled AWS ECS Fargate task.

## What gets created

- VPC with 2 public subnets
- Security group for outbound-only task networking
- ECS cluster and Fargate task definition
- CloudWatch log group for task logs
- EventBridge schedule rule that runs the task periodically
- IAM roles and policies for ECS task execution and EventBridge invocation

## Prerequisites

- Terraform 1.6+
- AWS credentials configured (for example via AWS CLI profile)
- A container image that includes this repository code and Python dependencies

## Files

- main.tf: Core infrastructure resources
- variables.tf: Input variables
- outputs.tf: Useful output values
- versions.tf: Terraform and AWS provider versions
- terraform.tfvars.example: Example variable values

## Quick start

1. Copy tfvars example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

2. Edit terraform.tfvars and set at minimum:

- container_image
- llm_provider
- provider-specific endpoint and API key

3. Initialize and deploy:

```bash
terraform init
terraform plan
terraform apply
```

## Notes

- The task command runs:

```bash
python scripts/fraud_agent_langchain.py --report <report_path> --dataset <dataset_path> --random-state <random_state> [provider args]
```

- OpenAI-compatible mode (llm_provider = "openai_compatible") provider args:

```bash
--llm-provider openai_compatible --base-url <openai_base_url> --model <openai_model> --api-key <openai_api_key>
```

- Azure AI Foundry mode (llm_provider = "azure_foundry") provider args:

```bash
--llm-provider azure_foundry --azure-endpoint <azure_endpoint> --azure-deployment <azure_deployment> --azure-api-version <azure_api_version> --azure-api-key <azure_api_key>
```

- dataset_path and report_path are paths inside the container image.
- If your model endpoint is only reachable in a private network, move this task to private subnets and add NAT or VPC endpoints.
