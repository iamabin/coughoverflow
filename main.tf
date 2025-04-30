


terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }

  }
}

provider "aws" {
  region = "us-east-1"
  shared_credentials_files = ["./credentials"]
  default_tags {
    tags = {
      Course     = "CSSE6400"
      Name       = "CoughOverflow"
      Automation = "Terraform"
    }
  }
}

data "aws_ecr_authorization_token" "ecr_token" {}


provider "docker" {
  registry_auth {
    address  = data.aws_ecr_authorization_token.ecr_token.proxy_endpoint
    username = data.aws_ecr_authorization_token.ecr_token.user_name
    password = data.aws_ecr_authorization_token.ecr_token.password
  }
}

resource "aws_ecr_repository" "coughoverflow" {
  name = "coughoverflow"
}



resource "docker_image" "coughoverflow" {
  name = "${aws_ecr_repository.coughoverflow.repository_url}:latest"
  build {
    context = "."
    dockerfile = "Dockerfile"
    platform = "linux/amd64"

  }
}


resource "docker_registry_image" "coughoverflow" {
  name = docker_image.coughoverflow.name
}



locals {
  image_name = docker_image.coughoverflow.name
}






data "aws_iam_role" "lab" {
  name = "LabRole"
}


data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}


resource "aws_security_group" "coughoverflow" {
  name        = "coughoverflow"
  description = "Allow HTTP access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 8080
    to_port   = 8080
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Allow ECS services to access RDS"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL from ECS"
    from_port   = 5432
    to_port     = 5432
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

resource "aws_db_instance" "coughoverflow_db" {
  identifier             = "coughoverflow-db"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "17.2"
  instance_class         = "db.t3.micro"
  name                   = "coughoverflow"
  username               = "coughuser"
  password               = "Adminpassword123"
  publicly_accessible    = true
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name
}

resource "aws_db_subnet_group" "default" {
  name       = "default-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
}


resource "aws_lb" "coughoverflow" {
  name               = "coughoverflow-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups = [aws_security_group.coughoverflow.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "coughoverflow" {
  name        = "coughoverflow-tg"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    path = "/api/v1/health"
    # matcher             = "200-499"

    port                = "8080"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 10
  }
}

resource "aws_lb_listener" "coughoverflow" {
  load_balancer_arn = aws_lb.coughoverflow.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.coughoverflow.arn
  }
}

resource "aws_ecs_cluster" "coughoverflow" {
  name = "coughoverflow"
}


resource "aws_ecs_task_definition" "coughoverflow" {
  family             = "coughoverflow"
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                = 1024
  memory             = 2048
  execution_role_arn = data.aws_iam_role.lab.arn
  depends_on = [docker_registry_image.coughoverflow]

  container_definitions = <<DEFINITION
  [
    {
      "name": "coughoverflow",
      "image": "${local.image_name}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/coughoverflow/todo",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "environment": [
        {
          "name": "SQLALCHEMY_DATABASE_URI",
          "value": "postgresql://coughuser:Adminpassword123@${aws_db_instance.coughoverflow_db.address}:5432/coughoverflow"
        }
      ]
    }
  ]
  DEFINITION
}

resource "aws_ecs_service" "coughoverflow" {
  name            = "coughoverflow"
  cluster         = aws_ecs_cluster.coughoverflow.id
  task_definition = aws_ecs_task_definition.coughoverflow.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups = [aws_security_group.coughoverflow.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.coughoverflow.arn
    container_name   = "coughoverflow"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.coughoverflow]
}




resource "aws_appautoscaling_target" "coughoverflow" {
  max_capacity       = 15
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.coughoverflow.name}/${aws_ecs_service.coughoverflow.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu_policy" {
  name               = "coughoverflow-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.coughoverflow.resource_id
  scalable_dimension = aws_appautoscaling_target.coughoverflow.scalable_dimension
  service_namespace  = aws_appautoscaling_target.coughoverflow.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 20.0
  }
}





resource "local_file" "api_txt" {
  content  = "http://${aws_lb.coughoverflow.dns_name}/api/v1"
  filename = "./api.txt"
}

output "api_url" {
  value = "http://${aws_lb.coughoverflow.dns_name}/api/v1"

}
output "rds_endpoint" {
  value = aws_db_instance.coughoverflow_db.endpoint
}