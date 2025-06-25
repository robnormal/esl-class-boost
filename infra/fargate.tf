locals {
  service_configs = {
    api = {
      cpu            = "512"
      memory         = "1024"
      repository_name = "learning-tool-api"
      image_tag      = "0.1.8"
    }
    paragraphs = {
      cpu            = "512"
      memory         = "1024"
      repository_name = "learning-tool-paragraphs"
      image_tag      = "0.1.5"
    }
    summaries = {
      cpu            = "512"
      memory         = "1024"
      repository_name = "learning-tool-summaries"
      image_tag      = "0.1.1"
    }
    vocabulary = {
      cpu            = "512"
      memory         = "1024"
      repository_name = "learning-tool-vocabulary"
      image_tag      = "0.1.1"
    }
  }
}

data "aws_ssm_parameter" "aws_secret_access_key" {
  name = "/learning-tool/aws_secret_access_key"
  with_decryption = true
}
data "aws_ssm_parameter" "aws_access_key_id" {
  name = "/learning-tool/aws_access_key_id"
  with_decryption = true
}
data "aws_ssm_parameter" "gcp_documentai_credentials" {
  name = "/learning-tool/gcp_documentai_credentials"
  with_decryption = true
}
data "aws_ssm_parameter" "gcp_project_id" {
  name = "/learning-tool/gcp_project_id"
  with_decryption = true
}
data "aws_ssm_parameter" "gcp_layout_parser_processor_id" {
  name = "/learning-tool/gcp_layout_parser_processor_id"
  with_decryption = true
}
data "aws_ssm_parameter" "openai_api_key" {
  name = "/learning-tool/openai_api_key"
  with_decryption = true
}

## VPC ##

# ECS needs a VPC, Subnets, Security Groups
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "fargate_sg" {
  name        = "fargate-sg"
  description = "Allow HTTP traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


## ECS

# ECS Cluster
resource "aws_ecs_cluster" "learning_tool_ecs_cluster" {
  name = "learning-tool-cluster"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "learning_tool_log_group" {
  name              = "/ecs/learning-tool"
  retention_in_days = 30
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
        Principal = { Service = "ecs-tasks.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Inline policy for CloudWatch Logs permissions
resource "aws_iam_role_policy" "ecs_logs_policy" {
  name = "ecs-logs-policy"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect = "Allow"
        Resource = "arn:aws:logs:*:*:log-group:/ecs/learning-tool:*"
      },
      {
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Effect = "Allow"
        Resource = [
          for repo in aws_ecr_repository.repos : repo.arn
        ]
      }
    ]
  })
}

# Policy for reading parameters from SSM
resource "aws_iam_role_policy" "ecs_ssm_policy" {
  name = "ecs-ssm-policy"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "ssm:GetParametersByPath"
        ]
        Effect = "Allow"
        Resource = "arn:aws:ssm:us-east-2:${data.aws_caller_identity.current.account_id}:parameter/learning-tool/*"
      }
    ]
  })
}

# ECS Tasks - one for each microservice

resource "aws_ecs_task_definition" "tasks" {
  for_each = local.service_configs

  family                   = "learning-tool-${each.key}"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name         = "${each.key}-task"
      image        = "${aws_ecr_repository.repos[each.key].repository_url}:${each.value.image_tag}"
      portMappings = [{ containerPort = 80, hostPort = 80 }]
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "FLASK_PORT", value = "80" },
        { name = "SUBMISSIONS_BUCKET", value = "${aws_s3_bucket.submissions.bucket}" },
        { name = "PARAGRAPHS_BUCKET", value = "${aws_s3_bucket.paragraphs.bucket}" },
        { name = "AWS_ACCOUNT_ID", value = data.aws_caller_identity.current.account_id },
        { name = "AWS_REGION", value = data.aws_region.current.name },
        { name = "AWS_DEFAULT_REGION", value = data.aws_region.current.name },
        { name = "COGNITO_USERPOOL_ID", value = aws_cognito_user_pool.user_pool.id },
        { name = "COGNITO_APP_CLIENT_ID", value = aws_cognito_user_pool_client.user_pool_client.id },
        { name = "GCP_LOCATION", value = "us" },
        { name = "CORS_ORIGINS", value = "https://${aws_cloudfront_distribution.website.domain_name}" }
      ]
      secrets = [
        { name = "AWS_SECRET_ACCESS_KEY", valueFrom = data.aws_ssm_parameter.aws_secret_access_key.arn },
        { name = "AWS_ACCESS_KEY_ID", valueFrom = data.aws_ssm_parameter.aws_access_key_id.arn },
        { name = "GCP_DOCUMENTAI_CREDENTIALS", valueFrom = data.aws_ssm_parameter.gcp_documentai_credentials.arn },
        { name = "GCP_PROJECT_ID", valueFrom = data.aws_ssm_parameter.gcp_project_id.arn },
        { name = "GCP_LAYOUT_PARSER_PROCESSOR_ID", valueFrom = data.aws_ssm_parameter.gcp_layout_parser_processor_id.arn },
        { name = "OPENAI_API_KEY", valueFrom = data.aws_ssm_parameter.openai_api_key.arn }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/learning-tool"
          "awslogs-region"        = "us-east-2"
          "awslogs-stream-prefix" = each.key
        }
      }
    }
  ])
}

## ECR

resource "aws_ecr_repository" "repos" {
  for_each = local.service_configs

  name                 = each.value.repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = each.value.repository_name
  }
}

# Load Balancer for the API
resource "aws_lb" "app_alb" {
  name               = "learning-tool-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.fargate_sg.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "api_alb_group" {
  name        = "api-target-group"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"
  health_check {
    path                = "/api/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_alb_group.arn
  }
}

# ECS services
resource "aws_ecs_service" "api_ecs_service" {
  name            = "api-ecs-service"
  cluster         = aws_ecs_cluster.learning_tool_ecs_cluster.id
  task_definition = aws_ecs_task_definition.tasks["api"].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.fargate_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_alb_group.arn
    container_name   = "api-task"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "ecs_services" {
  for_each = toset(["paragraphs", "summaries", "vocabulary"])

  name            = "${each.value}-ecs-service"
  cluster         = aws_ecs_cluster.learning_tool_ecs_cluster.id
  task_definition = aws_ecs_task_definition.tasks[each.value].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.fargate_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_lb_listener.http]
}

## S3 Access

resource "aws_s3_bucket_policy" "paragraphs" {
  bucket = aws_s3_bucket.paragraphs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_execution.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.paragraphs.arn}",
          "${aws_s3_bucket.paragraphs.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_s3_bucket_policy" "summaries" {
  bucket = aws_s3_bucket.summaries.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_execution.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.summaries.arn}",
          "${aws_s3_bucket.summaries.arn}/*"
        ]
      }
    ]
  })
}

output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}
