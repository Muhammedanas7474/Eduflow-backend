# Eduflow AWS Deployment Guide

This guide outlines a scalable and modern architecture for deploying the Eduflow application (Django, FastAPI, Celery, Redis, PostgreSQL + pgvector) to AWS.

## Approach: Containerized Deployment (ECS Fargate)

Since your application is already containerized using `docker-compose`, the most natural and professional way to deploy it to AWS is using **Amazon ECS (Elastic Container Service)** with **Fargate** (serverless containers). This completely eliminates the need to manage EC2 instances.

---

## 1. Architecture Components

Here is how each piece of your `docker-compose.yml` translates to AWS services:

| Local Docker Service | AWS Service | Why |
| :--- | :--- | :--- |
| `backend` (Django) | **ECS Fargate** (Service 1) | Runs the Django backend containers seamlessly. Scales up/down automatically based on traffic. |
| `ai-service` (FastAPI) | **ECS Fargate** (Service 2) | Dedicated service for AI queries. |
| `celery_worker`, `ai-celery-worker`, `celery_beat` | **ECS Fargate** (Background Tasks) | Run as background workers pulling from Redis/SQS. |
| `nginx` | **Application Load Balancer (ALB)** | Replaces Nginx. ALB handles HTTPS (SSL certificates via ACM) and routes traffic to the correct ECS services (e.g., `/api/v1/` to Django, `/api/v1/rag/` to AI service). |
| `db` (Postgres + pgvector) | **Amazon RDS for PostgreSQL** | Managed, highly available, automated backups. **RDS PostgreSQL supports the `pgvector` extension natively.** |
| `redis` | **Amazon ElastiCache (Redis)** | Fully managed Redis cluster for Celery task queuing and caching. |
| Media / VOD storage | **Amazon S3** | You are already using S3 (`eduflow-videos-2026`). Continue this for videos, PDFs, and static files. |
| Emails & Notifications | **Amazon SES & SNS** | For Django email dispatch and push notifications. |

-

## 2. Step-by-Step Implementation Flow

### Phase 1: Preparation (Infrastructure Setup)
1. **Create an RDS Database:**
   - Go to AWS RDS. Create a PostgreSQL 15+ database.
   - Attach it to your default VPC.
   - Once created, connect to it and run `CREATE EXTENSION IF NOT EXISTS vector;` to enable `pgvector`.
2. **Create ElastiCache (Redis):**
   - Go to Amazon ElastiCache and create a Redis OSS cluster.
   - Ensure it is in the same VPC as the RDS instance.
3. **Register a Domain & SSL:**
   - If you don't have one, register a domain via Amazon Route 53.
   - Use **AWS Certificate Manager (ACM)** to request a free SSL certificate for your domain (e.g., `api.youreduflow.com`).

### Phase 2: Application Packaging
1. **Prepare `settings.py` for Production:**
   - Set `DEBUG = False`.
   - Update `ALLOWED_HOSTS` to include your new domain.
   - Configure your Django backend to serve static files using an S3 bucket (using `django-storages` or `whitenoise`).
2. **Create ECR Repositories (Elastic Container Registry):**
   - In AWS ECR, create two repositories: `eduflow-backend` and `eduflow-ai-service`.
3. **Build & Push Docker Images:**
   - Authenticate Docker to your ECR.
   - Build your backend image: `docker build -t eduflow-backend ./backend`
   - Tag and push it to the ECR repo.
   - Repeat for the `ai-service`.

### Phase 3: Deployment (ECS)
1. **Create an ECS Cluster:**
   - In AWS ECS, create a new "Fargate" cluster.
2. **Setup Task Definitions:**
   - A Task Definition is the AWS equivalent of a block in `docker-compose.yml`.
   - Create a Task Definition for the **Web Backend**. Map it to the ECR Image, expose port 8000, and inject environment variables (DB URL, Redis URL, Secret Keys).
   - Create a Task Definition for the **AI Service**.
   - Create Task Definitions for the **Celery Workers** and **Celery Beat**.
3. **Setup the Application Load Balancer (ALB):**
   - Create an ALB. Attach your ACM SSL Certificate to listen on Port 443 (HTTPS).
   - Configure routing rules: requests to the main backend go to a Backend Target Group, and AI requests go to an AI Target Group.
4. **Launch ECS Services:**
   - Run the Web Backend and AI Service Task Definitions as **ECS Services**. Attach them to the Load Balancer Target Groups.
   - Run the Celery Workers as ECS Services (no load balancer needed since they just listen to ElastiCache).

### Phase 4: CI/CD Automation (Optional but Recommended)
Set up **GitHub Actions** (or AWS CodePipeline). Whenever you push to the `main` branch:
1. GitHub Actions logs into AWS.
2. Builds the new Docker images.
3. Pushes them to ECR.
4. Tells ECS to trigger a new deployment to roll out the update with zero downtime.

---

## 3. Alternative (Easier/Cheaper Option for Early Stage)

If the ECS + RDS + ElastiCache setup feels too complex or expensive for an initial launch, there is a much simpler monolithic approach using a single **EC2 Instance**.

**The EC2 Approach:**
1. Spin up a single AWS EC2 instance (e.g., `t3.medium` or `t3.large`).
2. SSH into the server and install Docker and Docker Compose.
3. Clone your GitHub repository.
4. Copy your `.env.docker` files to the server.
5. Run `docker-compose up -d --build`.
   *(You'll need a reverse proxy like Nginx-Proxy-Manager or Caddy to handle SSL easily on the EC2 instance).*

**Verdict:** 
- Use **EC2** if you are just launching, have a low budget, and want to mirror your local environment exactly as it runs now.
- Use **ECS Fargate + RDS** (the main guide above) if you have paying customers, need high availability, automatic scaling, and secure managed databases without worrying about server crashes.
