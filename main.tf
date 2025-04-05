# terraform {
#     required_providers {
#         aws = {
#             source  = "hashicorp/aws"
#             version = "~> 4.0"
#         }
#     }
# }
#
# provider "aws" {
#     region = "us-east-1"
#     shared_credentials_files = ["./credentials"]
#     default_tags {
#         tags = {
#             Course       = "CSSE6400"
#             Name         = "CoughOverflow"
#             Automation   = "Terraform"
#         }
#     }
# }
#
# resource "local_file" "url" {
#     content  = "http://my-url/"  # Replace this string with a URL from your Terraform.
#     filename = "./api.txt"
# }


terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

provider "aws" {
  region                  = "us-east-1"
  shared_credentials_files = ["./credentials"]
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
  }
}

resource "docker_registry_image" "coughoverflow" {
  name = docker_image.coughoverflow.name
}
