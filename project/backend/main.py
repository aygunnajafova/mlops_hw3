import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Azercell Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    sources: Optional[list[dict[str, Any]]] = []

class SearchRequest(BaseModel):
    query: str

AWS_CONFIG = {
    'region': os.getenv('AWS_REGION', 'us-east-1'),
    'access_key': os.getenv('AWS_ACCESS_KEY_ID', ''),
    'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
}

bedrock_client = None
bedrock_knowledge_base = None
knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID', 'JGMPKF6VEI')

def init_aws_clients():
    global bedrock_client, bedrock_knowledge_base
    try:
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_CONFIG['region'],
            aws_access_key_id=AWS_CONFIG['access_key'],
            aws_secret_access_key=AWS_CONFIG['secret_key'],
        )

        bedrock_knowledge_base = boto3.client(
            "bedrock-agent-runtime",
            region_name=AWS_CONFIG['region'],
            aws_access_key_id=AWS_CONFIG['access_key'],
            aws_secret_access_key=AWS_CONFIG['secret_key'],
        )
        logger.info("AWS clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")

@app.on_event("startup")
async def startup_event():
    init_aws_clients()

def create_body_json(messages, max_tokens=1024, system=None, temperature=0.5):
    body_dict = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        body_dict['system'] = system
    return json.dumps(body_dict)

def get_knowledge_base_data(user_query: str) -> str:
    """Retrieve Azercell policy and corporate information from the Bedrock Knowledge Base."""
    try:
        req = {
            "knowledgeBaseId": knowledge_base_id,
            "retrievalQuery": {"text": user_query},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": 3
                }
            }
        }
        response = bedrock_knowledge_base.retrieve(**req)
        candidates = response.get("retrievalResults", [])

        if not candidates:
            return "No relevant information found in the knowledge base."

        vec_response = '\n\n'.join([
            f'Document {ind+1}: ' + i.get('content', {}).get('text', '')
            for ind, i in enumerate(candidates)
        ])
        return vec_response
    except Exception as e:
        logger.error(f"Error retrieving from knowledge base: {e}")
        return f"Error accessing knowledge base: {str(e)}"

def chat_with_bedrock(messages: list[dict], system: Optional[str] = None) -> str:
    """Chat with Bedrock Claude model."""
    try:
        model = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
        body_json = create_body_json(messages, system=system)

        response = bedrock_client.invoke_model(
            modelId=model,
            body=body_json
        )

        message = json.loads(response['body'].read().decode('utf-8'))
        return message['content'][0]['text']
    except Exception as e:
        logger.error(f"Error chatting with Bedrock: {e}")
        return f"Error communicating with AI model: {str(e)}"

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status():
    """Status endpoint for health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/search")
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base for relevant information."""
    try:
        if not bedrock_knowledge_base:
            raise HTTPException(status_code=500, detail="Knowledge base client not initialized")

        results = get_knowledge_base_data(request.query)
        return {"query": request.query, "results": results}
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint with knowledge base integration."""
    try:
        if not bedrock_client:
            raise HTTPException(status_code=500, detail="Bedrock client not initialized")

        messages = []
        if request.conversation_history:
            messages.extend([msg.dict() for msg in request.conversation_history])

        messages.append({"role": "user", "content": request.message})

        kb_info = get_knowledge_base_data(request.message)

        enhanced_message = f"""
        ### Knowledge Base Information:
        {kb_info}

        ### User Question:
        {request.message}

        Please provide a helpful response based on the knowledge base information above. If the information is not sufficient, use your general knowledge to provide a helpful response.
        """

        messages[-1]["content"] = enhanced_message

        system_prompt = """You are a helpful AI assistant for Azercell Telecom. You have access to company policies, procedures, and information. Always provide accurate, helpful responses based on the available information. Be professional and courteous."""

        response = chat_with_bedrock(messages, system=system_prompt)

        return ChatResponse(
            response=response,
            sources=[{"type": "knowledge_base", "content": kb_info}]
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint."""
    try:
        if not bedrock_client:
            raise HTTPException(status_code=500, detail="Bedrock client not initialized")

        messages = []
        if request.conversation_history:
            messages.extend([msg.dict() for msg in request.conversation_history])

        messages.append({"role": "user", "content": request.message})

        kb_info = get_knowledge_base_data(request.message)

        enhanced_message = f"""
        ### Knowledge Base Information:
        {kb_info}

        ### User Question:
        {request.message}

        Please provide a helpful response based on the knowledge base information above.
        """

        messages[-1]["content"] = enhanced_message

        model = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
        body_json = create_body_json(messages)

        stream = bedrock_client.invoke_model_with_response_stream(
            modelId=model,
            body=body_json
        )

        async def generate_stream():
            try:
                stream_body = stream.get("body")
                for event in stream_body:
                    stream_chunk = event.get("chunk")
                    if stream_chunk:
                        decoded = json.loads(stream_chunk.get("bytes").decode("utf-8"))
                        delta = decoded.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield f"data: {json.dumps({'text': text})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    except Exception as e:
        logger.error(f"Streaming chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
