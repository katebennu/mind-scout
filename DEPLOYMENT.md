# MindScout Deployment Guide

## Quick Start Options

### Option 1: Single VPS Deployment (Recommended for Personal Use)

**Requirements**:
- VPS with 1GB RAM, 20GB storage (DigitalOcean, Linode, Hetzner)
- Domain name (optional but recommended)
- SSH access

**Cost**: $5-10/month

#### Step 1: Provision Server

```bash
# Create a new Ubuntu 22.04 server
# SSH into your server
ssh root@your-server-ip
```

#### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Node, Nginx, PostgreSQL
sudo apt install -y python3.10 python3-pip nodejs npm nginx postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Start services
sudo systemctl start postgresql redis-server nginx
sudo systemctl enable postgresql redis-server nginx
```

#### Step 3: Setup PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE mindscout;
CREATE USER mindscout WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE mindscout TO mindscout;
\q
```

#### Step 4: Clone and Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/mindscout
sudo chown $USER:$USER /opt/mindscout

# Clone repository
git clone https://github.com/yourusername/mindscout.git /opt/mindscout
cd /opt/mindscout

# Install Python dependencies
pip3 install -e .
pip3 install gunicorn psycopg2-binary

# Setup environment variables
cat > .env << EOF
DATABASE_URL=postgresql://mindscout:your-secure-password@localhost/mindscout
ANTHROPIC_API_KEY=your-anthropic-key
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

#### Step 5: Migrate to PostgreSQL

**Update database.py**:

```python
# Change from SQLite to PostgreSQL
from mindscout.config import get_env

DATABASE_URL = get_env("DATABASE_URL", f"sqlite:///{DB_PATH}")
engine = create_engine(DATABASE_URL)
```

**Run migrations**:

```bash
# Initialize database
python3 -c "from mindscout.database import init_db; init_db()"

# Optional: Import existing SQLite data
python3 scripts/migrate_sqlite_to_postgres.py
```

#### Step 6: Build Frontend

```bash
cd /opt/mindscout/frontend

# Install dependencies
npm install

# Update API endpoint
# Edit frontend/src/config.ts
cat > src/config.ts << EOF
export const API_BASE_URL = process.env.VITE_API_URL || 'https://yourdomain.com/api';
EOF

# Build for production
npm run build

# Copy to nginx directory
sudo mkdir -p /var/www/mindscout
sudo cp -r dist/* /var/www/mindscout/
```

#### Step 7: Configure Systemd Service

```bash
sudo nano /etc/systemd/system/mindscout-api.service
```

**Service file content**:

```ini
[Unit]
Description=MindScout API Server
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mindscout
EnvironmentFile=/opt/mindscout/.env
ExecStart=/usr/local/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Start the service**:

```bash
sudo systemctl daemon-reload
sudo systemctl start mindscout-api
sudo systemctl enable mindscout-api
sudo systemctl status mindscout-api
```

#### Step 8: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/mindscout
```

**Nginx configuration**:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        root /var/www/mindscout;
        try_files $uri $uri/ /index.html;

        # Caching for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

**Enable the site**:

```bash
sudo ln -s /etc/nginx/sites-available/mindscout /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 9: Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
```

#### Step 10: Setup Scheduled Fetching (Optional)

**Create worker service**:

```bash
sudo nano /etc/systemd/system/mindscout-worker.service
```

```ini
[Unit]
Description=MindScout Background Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mindscout
EnvironmentFile=/opt/mindscout/.env
ExecStart=/usr/local/bin/celery -A mindscout.tasks worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Create scheduler service**:

```bash
sudo nano /etc/systemd/system/mindscout-beat.service
```

```ini
[Unit]
Description=MindScout Task Scheduler
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mindscout
EnvironmentFile=/opt/mindscout/.env
ExecStart=/usr/local/bin/celery -A mindscout.tasks beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Option 2: Docker Deployment

**Requirements**:
- Docker and Docker Compose installed
- Domain name
- Cloud provider (AWS, GCP, DigitalOcean, etc.)

#### Step 1: Create Docker Files

**Backend Dockerfile**:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN pip install -e .

# Run migrations on startup
CMD ["sh", "-c", "python -c 'from mindscout.database import init_db; init_db()' && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
```

**Frontend Dockerfile**:

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**: (See above in Option 3)

#### Step 2: Deploy

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

### Option 3: Serverless Deployment

**Frontend → Vercel/Netlify**:

```bash
cd frontend

# For Vercel
vercel

# For Netlify
netlify deploy --prod
```

**Backend → Railway**:

1. Connect GitHub repo to Railway
2. Add environment variables
3. Deploy automatically on push

---

## MCP Server Deployment

The MCP server is designed to run **locally** on each user's machine to integrate with Claude Desktop.

### For Multi-User Setup:

**Option A**: Each user runs their own MCP server locally
- Server connects to shared backend API
- User authentication via API keys

**Option B**: Replace MCP with Web-based Claude integration
- Use Claude API directly from backend
- Provide web interface for AI interactions
- Remove dependency on Claude Desktop

---

## Monitoring & Maintenance

### Setup Monitoring

```bash
# Install monitoring tools
pip install prometheus-client
pip install sentry-sdk[fastapi]
```

**Add to backend/main.py**:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
)
```

### Backup Strategy

```bash
# Daily PostgreSQL backups
crontab -e

# Add:
0 2 * * * pg_dump mindscout > /backups/mindscout_$(date +\%Y\%m\%d).sql
```

### Logs

```bash
# View API logs
sudo journalctl -u mindscout-api -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Security Checklist

- [ ] Use strong passwords for database
- [ ] Enable firewall (ufw)
- [ ] Setup SSL/TLS (Let's Encrypt)
- [ ] Use environment variables for secrets
- [ ] Enable CORS properly
- [ ] Rate limiting on API
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor error logs

---

## Scaling Considerations

### When to scale:

**100+ users**:
- Add Redis for caching
- Use CDN for frontend
- Database read replicas

**1000+ users**:
- Load balancer
- Multiple backend instances
- Dedicated database server
- Background job queues

**10,000+ users**:
- Kubernetes orchestration
- Microservices architecture
- Distributed caching
- Database sharding

---

## Cost Estimates

### Personal Use:
- **DigitalOcean Droplet**: $6/month
- **Domain**: $12/year
- **Total**: ~$7/month

### Small Team (10 users):
- **VPS**: $12/month
- **Backups**: $2/month
- **Domain**: $12/year
- **Total**: ~$15/month

### Production (1000 users):
- **App servers** (3x): $36/month
- **Database**: $15/month
- **Redis**: $10/month
- **CDN**: $20/month
- **Monitoring**: $15/month
- **Total**: ~$100/month

---

## Troubleshooting

### API won't start:
```bash
# Check logs
sudo journalctl -u mindscout-api -n 50

# Test manually
cd /opt/mindscout
python -m uvicorn backend.main:app
```

### Database connection issues:
```bash
# Test PostgreSQL
psql -U mindscout -d mindscout -h localhost

# Check service
sudo systemctl status postgresql
```

### Frontend 404 errors:
```bash
# Check nginx config
sudo nginx -t

# Verify files
ls -la /var/www/mindscout
```

---

## Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Setup](https://www.postgresql.org/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)
