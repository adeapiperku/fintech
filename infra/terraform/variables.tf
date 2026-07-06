variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
  default     = "fintech-fraud-agent"
}

variable "container_image" {
  description = "Container image URI for the fraud agent, for example ECR URI"
  type        = string
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 1024
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for periodic runs"
  type        = string
  default     = "rate(15 minutes)"
}

variable "dataset_path" {
  description = "Path to dataset inside the container"
  type        = string
  default     = "fintech.csv"
}

variable "report_path" {
  description = "Path to report file inside the container"
  type        = string
  default     = "samples/sample_report.txt"
}

variable "llm_provider" {
  description = "LLM backend mode: openai_compatible or azure_foundry"
  type        = string
  default     = "openai_compatible"

  validation {
    condition     = contains(["openai_compatible", "azure_foundry"], var.llm_provider)
    error_message = "llm_provider must be either openai_compatible or azure_foundry."
  }
}

variable "openai_base_url" {
  description = "OpenAI-compatible endpoint used by the agent"
  type        = string
  default     = ""
}

variable "openai_model" {
  description = "Model name exposed by the OpenAI-compatible endpoint"
  type        = string
  default     = "local-model"
}

variable "openai_api_key" {
  description = "API key for the OpenAI-compatible endpoint"
  type        = string
  default     = "lm-studio"
  sensitive   = true
}

variable "azure_endpoint" {
  description = "Azure AI Foundry endpoint for chat completions"
  type        = string
  default     = ""
}

variable "azure_deployment" {
  description = "Azure AI Foundry deployment name"
  type        = string
  default     = ""
}

variable "azure_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2024-10-21"
}

variable "azure_api_key" {
  description = "API key for Azure AI Foundry"
  type        = string
  default     = ""
  sensitive   = true
}

variable "random_state" {
  description = "Random seed for RandomForest training"
  type        = number
  default     = 42
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated VPC"
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs used for Fargate networking"
  type        = list(string)
  default     = ["10.42.1.0/24", "10.42.2.0/24"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention for task logs"
  type        = number
  default     = 14
}
