# Terraform configuration for replacing Lambda with ECS Fargate + ALB

provider "aws" {
  region = "us-east-2"
}

# VPC, Subnets, Security Groups (use existing if defined elsewhere)
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
  description = "Allow HTTP from API Gateway"
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

# ECS Cluster
resource "aws_ecs_cluster" "app" {
  name = "history-learning-cluster"
}

# Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "flask" {
  family                   = "history-learning-flask"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "flask-app",
      image     = "your-docker-image-url", # Replace with ECR or public image
      portMappings = [{ containerPort = 80, hostPort = 80 }],
      environment = [
        { name = "FLASK_ENV", value = "production" },
      ]
    }
  ])
}

# Application Load Balancer
resource "aws_lb" "app_alb" {
  name               = "history-learning-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.fargate_sg.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "flask_tg" {
  name     = "flask-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id
  target_type = "ip"
  health_check {
    path                = "/health"
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
    target_group_arn = aws_lb_target_group.flask_tg.arn
  }
}

# ECS Service
resource "aws_ecs_service" "flask_service" {
  name            = "flask-fargate-service"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.flask.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.default.ids
    security_groups = [aws_security_group.fargate_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.flask_tg.arn
    container_name   = "flask-app"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}

# API Gateway Integration with ALB
resource "aws_api_gateway_integration" "alb_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "http://${aws_lb.app_alb.dns_name}"
}

resource "aws_api_gateway_integration" "alb_root_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_rest_api.api.root_resource_id
  http_method             = aws_api_gateway_method.proxy_root.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "http://${aws_lb.app_alb.dns_name}"
}

output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}
