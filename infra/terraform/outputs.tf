output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.this.name
}

output "ecs_task_definition_arn" {
  description = "Task definition ARN for the fraud agent"
  value       = aws_ecs_task_definition.agent.arn
}

output "event_rule_name" {
  description = "EventBridge schedule rule name"
  value       = aws_cloudwatch_event_rule.schedule.name
}

output "log_group_name" {
  description = "CloudWatch log group for agent execution logs"
  value       = aws_cloudwatch_log_group.agent.name
}

output "vpc_id" {
  description = "VPC ID used by the scheduled task"
  value       = aws_vpc.this.id
}
