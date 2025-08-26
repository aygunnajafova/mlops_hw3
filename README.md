# Azercell Telecom Chatbot

A powerful AI-powered chatbot for Azercell Telecom that provides instant access to company policies, procedures, and information using AWS Bedrock and Claude AI.

## Features

- **AI-Powered Chat**: Built with AWS Bedrock and Claude 3.7 Sonnet
- **Knowledge Base Integration**: Searches through Azercell company documents
- **Real-time Streaming**: Live response streaming for better user experience
- **Conversation History**: Maintains chat context across sessions
- **Knowledge Base Search**: Direct search through company documents
- **Export Conversations**: Download chat history as text files
- **Responsive UI**: Modern Streamlit interface with mobile support

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AWS Bedrock   │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   + Claude AI   │
│   Port: 8501    │    │   Port: 8000    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Knowledge      │
                       │  Base (RAG)     │
                       │  ID: JGMPKF6VEI │
                       └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- AWS Account with Bedrock access
- AWS credentials (Access Key & Secret Key)
- Knowledge Base ID (default: JGMPKF6VEI)

## Setup Instructions

### 1. Clone and Navigate
```bash
cd azercell-chatbot
```

### 2. Configure Environment Variables
```bash
cp env.example .env
```

Edit `.env` file with your AWS credentials:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
KNOWLEDGE_BASE_ID=JGMPKF6VEI
```

### 3. Build and Run with Docker
```bash
# Build and start services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## API Endpoints

### Chat Endpoints
- `POST /chat` - Regular chat with knowledge base integration
- `POST /chat/stream` - Streaming chat responses
- `GET /health` - Health check
- `GET /status` - Status endpoint

### Knowledge Base
- `POST /search` - Search company documents

## Docker Services

### Backend (FastAPI)
- **Port**: 8000
- **Container**: azercell-backend
- **Health Check**: `/status` endpoint

### Frontend (Streamlit)
- **Port**: 8501
- **Container**: azercell-frontend
- **Health Check**: `/_stcore/health` endpoint

## Usage

### 1. Start a Conversation
- Type your question in the chat input
- The AI will search the knowledge base for relevant information
- Responses are generated using both knowledge base data and AI capabilities

### 2. Knowledge Base Search
- Use the sidebar search feature to find specific information
- Results show relevant document excerpts

### 3. Export Conversations
- Download your chat history as text files
- Useful for record-keeping and analysis

## 🔍 Knowledge Base Integration

The chatbot integrates with AWS Bedrock Knowledge Base containing:
- Company policies and procedures
- Code of conduct and ethics
- Corporate values and vision
- Internal procedures and standards
- CEO messages and communications

## Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Check if backend container is running: `docker ps`
   - Verify AWS credentials in `.env` file
   - Check backend logs: `docker logs azercell-backend`

2. **Frontend Not Loading**
   - Ensure frontend container is healthy
   - Check frontend logs: `docker logs azercell-frontend`
   - Verify backend is accessible from frontend

3. **AWS Authentication Issues**
   - Verify AWS credentials are correct
   - Ensure AWS account has Bedrock access
   - Check AWS region configuration

### Debug Commands
```bash
# View all containers
docker ps

# View logs
docker logs azercell-backend
docker logs azercell-frontend

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up --build
```

## Security Notes

- AWS credentials are stored in environment variables
- Never commit `.env` file to version control
- Use IAM roles with minimal required permissions
- Enable AWS CloudTrail for audit logging

## Monitoring

- Health checks run every 30 seconds
- Services automatically restart on failure
- Logs are available via Docker commands
- Backend provides `/health` and `/status` endpoints

## Development

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Adding New Features
1. Modify backend endpoints in `backend/main.py`
2. Update frontend interface in `frontend/app.py`
3. Test locally before building Docker images
4. Update requirements.txt if adding new dependencies

## License

This project is proprietary to Azercell Telecom.

## Support

For technical support or questions:
- Check the troubleshooting section
- Review Docker logs for error details
- Verify AWS configuration and permissions

---

**Built with ❤️ using FastAPI, Streamlit, and AWS Bedrock**
