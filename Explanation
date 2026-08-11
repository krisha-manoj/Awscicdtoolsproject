
# AWS CI/CD Pipeline Project — Interview Explanation Guide

---

## 1. Project Overview (Opening Statement)

"I built a fully automated CI/CD pipeline using only AWS native tools. When I push code to the repository, the pipeline automatically builds a Docker image, stores it in a private registry, and deploys it to a serverless container platform — all without any manual intervention."

---

## 2. Architecture (Draw This on a Whiteboard)

```
Developer → CodeCommit → CodePipeline → CodeBuild → ECR → ECS Fargate
                              ↓
                    CloudWatch Event (auto-trigger on push)
```

**Detailed Flow:**
```
1. Developer pushes code to CodeCommit (main branch)
2. CloudWatch Event detects the push → triggers CodePipeline
3. CodePipeline Source Stage pulls the latest code
4. CodePipeline Build Stage triggers CodeBuild:
   - CodeBuild builds the Docker image
   - Pushes image to ECR with a unique tag (commit hash)
   - Generates imagedefinitions.json (tells ECS which image to use)
5. CodePipeline Deploy Stage:
   - Sends imagedefinitions.json to ECS
   - ECS performs a rolling update — launches new tasks with new image
   - Old tasks are drained and terminated
6. ALB routes traffic to healthy new containers
7. Application live with new version ✅
```

---

## 3. What Each File Does

### app.py — The Application

"This is a Python Flask web application. It has two routes:"
- `/` — serves the main HTML page showing the project details
- `/health` — returns `{"status": "healthy"}` — used by the ALB to check if the container is alive

```python
@app.route('/')
def home():
    return render_template('index.html', ...)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

"The health endpoint is critical — without it, the load balancer can't determine if the container is ready to receive traffic."

---

### requirements.txt — Dependencies

```
flask==3.0.0      # Web framework
gunicorn==21.2.0  # Production WSGI server
```

"Flask is the web framework. Gunicorn is the production-grade HTTP server — we don't use Flask's built-in server in production because it's single-threaded and not designed for real traffic."

---

### Dockerfile — Container Blueprint

```dockerfile
FROM python:3.11-slim       # Base image - lightweight Python
WORKDIR /app                # Set working directory
COPY requirements.txt .     # Copy deps first (Docker layer caching)
RUN pip install ...         # Install dependencies
COPY . .                    # Copy application code
EXPOSE 8080                 # Document the port
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]  # Start server
```

"I use a multi-step COPY pattern — copying requirements first and installing dependencies before copying the app code. This leverages Docker's layer caching — if only app code changes, Docker doesn't reinstall dependencies, making builds faster."

---

### buildspec.yml — CodeBuild Instructions

"This file tells CodeBuild exactly what to do in each phase:"

```yaml
phases:
  pre_build:    # Login to ECR, set variables
  build:        # Build and tag Docker image
  post_build:   # Push image to ECR, create deployment artifact
```

**Key points to explain:**
- **IMAGE_TAG** uses the commit hash (first 7 chars) — ensures unique, traceable images
- **imagedefinitions.json** — tells ECS which container name maps to which image URI
- CodeBuild runs in a managed environment — no servers to maintain

"The output artifact `imagedefinitions.json` is crucial — it's the contract between CodeBuild and ECS. It says: for container named `python-flask-app`, use this specific image URI."

---

### taskdef.json — ECS Task Definition

"This defines how the container runs on ECS:"

```json
{
  "family": "python-flask-app",
  "networkMode": "awsvpc",           // Each task gets its own ENI/IP
  "requiresCompatibilities": ["FARGATE"],  // Serverless compute
  "cpu": "256",                      // 0.25 vCPU
  "memory": "512",                   // 512 MB RAM
  "executionRoleArn": "...",         // Permissions to pull images from ECR
  "containerDefinitions": [{
    "name": "python-flask-app",
    "image": "...",                   // ECR image URI
    "portMappings": [{"containerPort": 8080}],
    "logConfiguration": {...}         // CloudWatch Logs
  }]
}
```

**Key points:**
- `awsvpc` network mode gives each task its own IP — required for Fargate
- `executionRoleArn` allows ECS to pull images from ECR and write logs
- Log configuration sends container stdout to CloudWatch for debugging

---

### templates/index.html — Frontend

"A responsive HTML page that displays the project architecture, tools used, and the pipeline flow. It uses Jinja2 templating to receive dynamic variables from Flask."

---

## 4. Infrastructure Components (Explain Each)

### Application Load Balancer (ALB)

"The ALB is the entry point for users. It:"
- Terminates TLS (HTTPS) — so containers don't need SSL certificates
- Distributes traffic across healthy containers
- Performs health checks on `/health` endpoint every 30 seconds
- Removes unhealthy containers from rotation automatically

"Traffic flow: Browser → HTTPS:443 (ALB) → HTTP:8080 (Container). The ALB handles the encryption, containers serve plain HTTP."

---

### ECS Fargate

"I chose Fargate because:"
- No EC2 instances to manage, patch, or scale
- Pay only for container runtime (CPU + memory per second)
- Automatic scaling — just change desired count
- Each task gets its own network interface — true isolation

---

### Target Groups

"Target groups tell the ALB where to route traffic:"
- Protocol: HTTP (not HTTPS — containers don't have TLS)
- Port: 8080 (matching container port)
- Health check: HTTP GET `/health` on port 8080
- If health check fails, ALB stops sending traffic to that container

---

### Security Groups (Network Security)

"I implemented defense-in-depth with two security groups:"

**ALB SG:** Only allows HTTPS:443 from my specific IP — no one else can access
**ECS Task SG:** Only allows port 8080 from the ALB SG — containers are not directly accessible from the internet

"This means even if someone knows the container's IP, they can't reach it directly — traffic must go through the ALB."

---

### ECR (Container Registry)

"ECR stores Docker images privately within my AWS account. Each build pushes an image tagged with the git commit hash — so every deployed version is traceable back to the exact code change that produced it."

---

## 5. IAM Roles (Security & Permissions)

"I follow the principle of least privilege with three separate roles:"

| Role | What It Can Do | Why |
|------|---------------|-----|
| `ecsTaskExecutionRole` | Pull images from ECR, write CloudWatch logs | ECS needs this to start containers |
| `CodeBuildServiceRole` | Read CodeCommit, push to ECR, write logs, access S3 (artifacts) | CodeBuild needs these to build and store artifacts |
| `ecsCodeDeployRole` | Manage ECS services, modify target groups | For Blue/Green deployments |

"Each service has only the permissions it needs — CodeBuild can't modify ECS services, ECS can't push images, etc."

---

## 6. How Deployment Works (Rolling Update)

"When CodePipeline triggers a deploy:"

1. ECS receives the new image URI from `imagedefinitions.json`
2. ECS launches new tasks with the new image
3. New tasks register with the target group
4. ALB health checks pass → new tasks marked healthy
5. ALB starts sending traffic to new tasks
6. Old tasks are drained (existing connections finish)
7. Old tasks are terminated

"There's zero downtime because the old containers keep serving until the new ones are ready."

---

## 7. Pipeline Trigger Mechanism

"I configured CloudWatch Events to watch the CodeCommit repository. When any commit is pushed to the `main` branch, it triggers the pipeline automatically. No webhooks to configure, no polling — it's event-driven and instant."

---

## 8. ACM Certificate (HTTPS)

"I imported a self-signed certificate to AWS Certificate Manager for the ALB's HTTPS listener. In production, you'd use ACM to generate a free certificate validated against a real domain using DNS validation. The self-signed cert demonstrates the TLS termination pattern — ALB handles HTTPS, containers serve HTTP."

---

## 9. Key Design Decisions (Interview Gold)

| Decision | Why |
|----------|-----|
| Fargate over EC2 | No server management, auto-scaling, pay-per-use |
| ALB over NLB | Need HTTP-level routing, health checks on specific paths |
| HTTPS on ALB, HTTP on containers | Simpler container setup, TLS termination is standard practice |
| Commit hash as image tag | Every deployment traceable to exact code change |
| Health endpoint (`/health`) | ALB can verify app is actually working, not just "port is open" |
| Separate security groups | Defense-in-depth, minimum blast radius |
| CloudWatch Logs | Centralized logging without SSH-ing into containers |

---

## 10. Challenges Faced & How I Solved Them

### Challenge 1: ALB Returning 504 Gateway Timeout
"Targets were healthy but ALB couldn't forward traffic. Root cause: target group was created with HTTPS protocol, but containers only serve HTTP. ALB was trying HTTPS to a container that doesn't do TLS. Fixed by recreating the target group with HTTP:8080."

### Challenge 2: Health Checks Failing
"Health checks were configured as HTTPS but containers serve HTTP. Changed health check protocol to HTTP — targets immediately became healthy."

### Challenge 3: Deploy Stage Failing
"The image definitions filename had a typo (`imagedefinations` vs `imagedefinitions`). Corrected the spelling in the pipeline configuration."

---

## 11. How to Extend This Project (Future Improvements)

- **Blue/Green Deployments:** Add CodeDeploy for zero-downtime deployments with instant rollback
- **Auto-Scaling:** Configure ECS Service Auto Scaling based on CPU/memory
- **Multi-Environment:** Separate pipelines for dev/staging/prod
- **Infrastructure as Code:** Use CloudFormation or Terraform to provision all resources
- **Monitoring:** Add CloudWatch alarms for 5xx errors, high latency
- **Secret Management:** Use AWS Secrets Manager for database credentials
- **Domain Name:** Route53 + ACM for a real domain with auto-renewed certificate

---

## 12. Quick Comparison (If Asked "Why Not Jenkins?")

| Aspect | Jenkins (Previous Project) | AWS Native (This Project) |
|--------|---------------------------|--------------------------|
| Infrastructure | Self-managed EC2 24/7 | Fully managed, serverless |
| Cost model | Pay for EC2 always-on | Pay per build minute |
| Maintenance | Patching, plugin updates, Java upgrades | Zero maintenance |
| Scaling | Manual | Automatic |
| Integration | Needs plugins for AWS | Native, first-class AWS integration |
| Setup complexity | High (Docker agent, SonarQube, credentials) | Low (IAM roles, buildspec) |

"I chose AWS native tools for this project because the entire infrastructure is managed — there's nothing to patch, no servers running 24/7, and the integration between services is seamless. For a team fully invested in AWS, this reduces operational overhead significantly."

---

## 13. Closing Statement

"This project demonstrates my ability to design and implement a production-ready CI/CD pipeline using cloud-native services. I understand container orchestration, networking (ALB, security groups, TLS termination), IAM security, and infrastructure automation. The pipeline is fully automated — a code push is the only manual action needed to deploy to production."
