# CoughOverflow 

A cloud-native application built on AWS for asynchronously analyzing saliva sample images to detect pathogens like COVID-19 or avian influenza (H5N1). It uses a microservices architecture and auto-scales to handle high traffic loads.

**Live API Endpoint:** `http://coughoverflow-alb-123456789.us-east-1.elb.amazonaws.com/api/v1` *(Note: Generated automatically after deployment)*

## Tech Stack

- **Infrastructure as Code (IaC):** Terraform
- **Containerization:** Docker
- **Cloud Platform:** AWS
- **Compute:** ECS Fargate (Serverless)
- **Database:** RDS (PostgreSQL)
- **Message Queue:** SQS (For decoupling and async processing)
- **Load Balancer:** Application Load Balancer (ALB)
- **Logging:** CloudWatch Logs
- **Security:** IAM Roles, Security Groups

## Project Structure

```
.
├── Dockerfile              # Main API service image
├── Dockerfile.worker       # Background worker image
├── main.py                 # Flask/FastAPI application
├── worker.py               # SQS message processor
├── deploy.sh               # One-click deployment script
├── terraform/              # Terraform configurations
...
├── api.txt                 # (Auto-generated) API endpoint URL
└── README.md               # This file
```



## Quick Start

### Prerequisites

1. An **AWS account** with CLI credentials configured (requires `LabRole` or appropriate permissions).
2. **Terraform** and **Docker** installed locally.

### One-Command Deployment

Clone the repo and run a single script to set up the entire infrastructure on AWS:



```
git clone https://github.com/iamabin/coughoverflow.git
cd coughoverflow
./deploy.sh
```



This script will:

1. Use Terraform to create all AWS resources (VPC, RDS, SQS, ALB, ECS, etc.).
2. Build Docker images and push them to ECR.
3. Deploy the API service and background worker to ECS Fargate.
4. Output the final API URL to `api.txt`.



## Architecture Highlights

1. **Decoupling & Async Processing:** The API service receives image analysis requests, stores them in the database, and immediately responds after sending job info to the SQS queue. The heavy image analysis is handled by a separate **Worker service** that processes tasks from the queue, preventing HTTP request blocking.
2. **Auto-Scaling:** The API service is configured with a CPU-based auto-scaling policy. It scales out instances during high traffic and scales in when traffic subsides, balancing performance and cost.
3. **Fully Managed:** Heavy use of Serverless (Fargate) and managed services (RDS, SQS) means no server maintenance, focusing purely on business logic.
4. **High Availability & Persistence:** Uses RDS PostgreSQL to ensure data persistence. Data remains safe even if all application instances crash.

## What Problem Does It Solve?

Traditional synchronous processing of computationally intensive tasks (like image analysis) can block servers, making them unresponsive to new requests. This project uses a **message queue (SQS)** and **async Workers** to decouple request handling from result computation. Even if analysis takes time, the API remains responsive, easily handling traffic spikes (e.g., during a disease outbreak).

## Notes

- This project was designed as an assignment for the university course *Software Architecture*.
- AWS resources are deployed in a Learner Lab environment. Be mindful of resource quotas and costs.
- It's recommended to click **"Reset Lab"** in the AWS console before deployment to ensure a clean environment.
