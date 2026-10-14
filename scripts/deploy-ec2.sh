#!/usr/bin/env bash
set -e

echo "=================================================="
echo "🚀 AegisAI AWS EC2 Automated Deployment Script"
echo "=================================================="

# 1. Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Docker not found. Installing Docker..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker "$USER" || true
    echo "✅ Docker installed successfully."
else
    echo "✅ Docker is already installed: $(docker --version)"
fi

# 2. Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "📦 Installing docker-compose-plugin..."
    sudo apt-get update -y
    sudo apt-get install -y docker-compose-plugin
fi
echo "✅ Docker Compose is available: $(docker compose version)"

# 3. Environment configuration
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️ Please edit .env with your GROQ_API_KEY and PINECONE_API_KEY if needed."
    fi
fi

# 4. Deploy containerized services
echo "🐳 Starting AegisAI services via Docker Compose..."
docker compose up -d --build

echo "⏳ Waiting 15 seconds for services to initialize..."
sleep 15

# 5. Display status
echo "=================================================="
echo "📊 Running Containers Status:"
docker compose ps

echo ""
echo "=================================================="
echo "🎉 AegisAI is deployed!"
echo "• FastAPI Backend:  http://$(hostname -I | awk '{print $1}'):8000"
echo "• API Swagger UI:   http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "• MLflow Dashboard: http://$(hostname -I | awk '{print $1}'):5000"
echo "• React Frontend:   http://$(hostname -I | awk '{print $1}'):5173"
echo "=================================================="
