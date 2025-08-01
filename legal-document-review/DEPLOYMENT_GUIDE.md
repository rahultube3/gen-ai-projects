# Legal Document Review System - Deployment Guide

## 🚀 **Deployment Overview**

This guide provides comprehensive instructions for deploying the Legal Document Review System across different environments, from local development to production deployment.

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11
- **Python**: 3.9 or higher
- **Node.js**: 18.0 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended for production)
- **Storage**: Minimum 50GB available space
- **Network**: Internet connection for package installation

### **Required Software**
```bash
# Core Dependencies
python3.9+
node.js 18+
npm 8+
git

# Optional (for containerized deployment)
docker
docker-compose

# Database
mongodb (local) or MongoDB Atlas (cloud)
```

## 🏠 **Local Development Deployment**

### **Step 1: Clone and Setup Repository**
```bash
# Clone the repository
git clone <repository-url>
cd legal-document-review

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for frontend
cd src/app  # Navigate to Angular app directory
npm install
cd ../..    # Return to project root
```

### **Step 2: Environment Configuration**
```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# Database Configuration
MONGODB_URL=mongodb://localhost:27017/legal_documents
DATABASE_NAME=legal_documents

# API Configuration
API_HOST=localhost
API_PORT=8000
DEBUG=true
SECRET_KEY=your-secret-key-here

# Frontend Configuration
FRONTEND_HOST=localhost
FRONTEND_PORT=4200

# Compliance Configuration
COMPLIANCE_LEVEL=standard
GUARDRAILS_API_KEY=your-guardrails-key
ENABLE_AUDIT_LOGGING=true

# Security Configuration
JWT_SECRET=your-jwt-secret-here
TOKEN_EXPIRY_HOURS=24
CORS_ORIGINS=http://localhost:4200

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### **Step 3: Database Setup**
```bash
# Start MongoDB (if running locally)
sudo systemctl start mongod  # Linux
brew services start mongodb  # macOS

# Initialize database and load sample data
python db_setup.py

# Verify database connection
python test_connection.py
```

### **Step 4: Start Backend Services**
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI backend
python main.py

# Or using uvicorn directly
uvicorn main:app --host localhost --port 8000 --reload
```

### **Step 5: Start Frontend Application**
```bash
# Navigate to Angular app directory
cd src/app

# Start development server
ng serve --host localhost --port 4200

# Or using npm
npm start
```

### **Step 6: Verify Deployment**
```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend accessibility
curl http://localhost:4200

# Run integration tests
python -m pytest tests/
```

## 🐳 **Docker Deployment**

### **Step 1: Docker Setup**
```bash
# Ensure Docker is installed and running
docker --version
docker-compose --version

# Build Docker images
docker-compose build

# Start services
docker-compose up -d
```

### **Docker Compose Configuration**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: 
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017/legal_documents
      - DEBUG=false
    depends_on:
      - mongo
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "4200:80"
    depends_on:
      - backend
    environment:
      - API_BASE_URL=http://backend:8000

  mongo:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=legal_documents

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  mongodb_data:
```

### **Step 2: Docker Health Checks**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Test services
curl http://localhost/health
curl http://localhost/
```

## ☁️ **Cloud Deployment (AWS)**

### **Prerequisites**
- AWS Account with appropriate permissions
- AWS CLI configured
- Domain name (optional, for custom SSL)

### **Step 1: Infrastructure Setup**

#### **EC2 Instance Configuration**
```bash
# Launch EC2 instance (t3.medium or larger recommended)
# Security Group Rules:
# - SSH (22): Your IP
# - HTTP (80): 0.0.0.0/0
# - HTTPS (443): 0.0.0.0/0
# - Custom (8000): 0.0.0.0/0 (API access)

# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip
```

#### **Instance Setup**
```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo yum install -y git
```

### **Step 2: Application Deployment**
```bash
# Clone repository
git clone <repository-url>
cd legal-document-review

# Configure environment for production
cp .env.example .env.production

# Edit production environment variables
nano .env.production
```

**Production Environment Variables:**
```bash
# Database (MongoDB Atlas recommended for production)
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/legal_documents
DATABASE_NAME=legal_documents

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
SECRET_KEY=your-production-secret-key

# Frontend Configuration
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=80

# Security Configuration
JWT_SECRET=your-production-jwt-secret
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem

# Compliance Configuration
COMPLIANCE_LEVEL=strict
GUARDRAILS_API_KEY=your-production-guardrails-key
ENABLE_AUDIT_LOGGING=true

# Monitoring
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-newrelic-key
```

### **Step 3: SSL Configuration**
```bash
# Install Certbot for Let's Encrypt
sudo yum install -y certbot

# Obtain SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Configure auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Step 4: Production Deployment**
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl https://yourdomain.com/health
curl https://yourdomain.com/
```

## 🏢 **Enterprise Production Deployment**

### **Kubernetes Deployment**

#### **Prerequisites**
- Kubernetes cluster (EKS, GKE, or AKS)
- kubectl configured
- Helm installed

#### **Step 1: Namespace Setup**
```bash
# Create namespace
kubectl create namespace legal-document-review

# Set default namespace
kubectl config set-context --current --namespace=legal-document-review
```

#### **Step 2: Deploy with Helm**
```bash
# Add Helm repository
helm repo add legal-docs ./helm-chart

# Install application
helm install legal-document-review legal-docs/legal-document-review \
  --set image.tag=latest \
  --set ingress.enabled=true \
  --set ingress.host=yourdomain.com \
  --set mongodb.enabled=false \
  --set mongodb.external.uri="mongodb+srv://..." \
  --set ssl.enabled=true
```

#### **Kubernetes Manifests Example**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: legal-backend
  template:
    metadata:
      labels:
        app: legal-backend
    spec:
      containers:
      - name: backend
        image: legal-document-review/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: uri
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📊 **Monitoring and Logging**

### **Application Monitoring**
```bash
# Health check endpoints
curl http://localhost:8000/health
curl http://localhost:4200/

# View application logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Monitor system resources
docker stats
```

### **Log Configuration**
```python
# logging.conf
[loggers]
keys=root,app,compliance,security

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=detailedFormatter,simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,rotatingFileHandler

[logger_app]
level=INFO
handlers=fileHandler
qualname=app
propagate=0

[logger_compliance]
level=DEBUG
handlers=fileHandler
qualname=compliance
propagate=0

[logger_security]
level=WARNING
handlers=fileHandler,consoleHandler
qualname=security
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log', 'a', 10485760, 5)

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_simpleFormatter]
format=%(levelname)s - %(message)s
```

## 🔧 **Troubleshooting**

### **Common Issues and Solutions**

#### **1. Backend Not Starting**
```bash
# Check Python dependencies
pip list | grep -E "(fastapi|uvicorn|pymongo)"

# Check environment variables
printenv | grep -E "(MONGODB|API|SECRET)"

# Check port availability
netstat -tulpn | grep :8000

# Solution: Ensure all dependencies installed and ports available
pip install -r requirements.txt
```

#### **2. Frontend Build Errors**
```bash
# Check Node.js version
node --version
npm --version

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Solution: Use compatible Node.js version (18+)
nvm install 18
nvm use 18
```

#### **3. Database Connection Issues**
```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').admin.command('ismaster'))"

# Check MongoDB status
sudo systemctl status mongod

# Solution: Ensure MongoDB is running and accessible
sudo systemctl start mongod
```

#### **4. Authentication Issues**
```bash
# Check JWT secret configuration
grep JWT_SECRET .env

# Test token generation
python -c "import jwt; print(jwt.encode({'user': 'test'}, 'secret', algorithm='HS256'))"

# Solution: Ensure consistent JWT secret across services
```

#### **5. SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in cert.pem -text -noout

# Test SSL configuration
curl -I https://yourdomain.com

# Solution: Renew certificates and restart services
sudo certbot renew
docker-compose restart
```

### **Performance Optimization**

#### **Backend Optimization**
```python
# Increase worker processes in production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Configure database connection pooling
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
```

#### **Frontend Optimization**
```bash
# Build for production with optimization
ng build --prod --aot --build-optimizer

# Enable gzip compression in Nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types application/json application/javascript text/css text/html;
```

#### **Database Optimization**
```javascript
// Create indexes for better search performance
db.documents.createIndex({ "text": "text" })
db.documents.createIndex({ "category": 1, "jurisdiction": 1 })
db.documents.createIndex({ "timestamp": -1 })
```

## 🛡️ **Security Checklist**

### **Pre-Production Security**
- [ ] SSL/TLS certificates configured
- [ ] Environment variables secured
- [ ] Database access restricted
- [ ] Authentication tokens encrypted
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Input validation enabled
- [ ] Audit logging active
- [ ] Compliance guardrails tested
- [ ] Security headers configured

### **Production Security**
```nginx
# nginx-security.conf
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';";
```

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
```yaml
# Load balancer configuration
apiVersion: v1
kind: Service
metadata:
  name: legal-backend-service
spec:
  selector:
    app: legal-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: legal-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: legal-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### **Database Scaling**
```javascript
// MongoDB sharding configuration
sh.enableSharding("legal_documents")
sh.shardCollection("legal_documents.documents", { "_id": "hashed" })

// Read replicas for search queries
db.documents.find().readPref("secondary")
```

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: July 31, 2025  
**Compatibility**: All deployment environments  
**Support**: DevOps Team
