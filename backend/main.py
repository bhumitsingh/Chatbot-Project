from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from model_config import MODELS
from chat_db import init_db, save_message
import requests
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

class ChatRequest(BaseModel):
    message: str
    model: str = "open_llama"
    session_id: str = "default"

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        logger.info(f"Received chat request: model={req.model}, session_id={req.session_id}")
        
        config = MODELS.get(req.model)
        if not config:
            logger.error(f"Model '{req.model}' not supported")
            raise HTTPException(status_code=400, detail=f"Model '{req.model}' not supported")

        user_message = req.message
        model_used = req.model
        session_id = req.session_id

        # Save user message
        try:
            save_message("user", user_message, model_used, session_id)
            logger.info("User message saved successfully")
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
            # Continue processing even if save fails

        # Process different model types
        if config["type"] == "huggingface":
            # Check if API key is set
            auth_header = config["headers"].get("Authorization", "")
            if "YOUR_HF_TOKEN" in auth_header:
                raise HTTPException(status_code=400, detail="HuggingFace API token not configured")
            
            payload = {
                "inputs": user_message,
                "parameters": {"max_new_tokens": 100}
            }
            
            try:
                response = requests.post(
                    config["url"], 
                    headers=config["headers"], 
                    json=payload, 
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats from HuggingFace
                if isinstance(data, list) and len(data) > 0:
                    if "generated_text" in data[0]:
                        text = data[0]["generated_text"]
                        # Remove the input prompt if it's included in the response
                        if text.startswith(user_message):
                            text = text[len(user_message):].strip()
                        if not text:  # If nothing left after removing prompt
                            text = "⚠️ No response generated."
                    else:
                        text = str(data[0])
                elif isinstance(data, dict) and "error" in data:
                    raise HTTPException(status_code=400, detail=f"HuggingFace API error: {data['error']}")
                else:
                    text = str(data)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"HuggingFace API request failed: {e}")
                raise HTTPException(status_code=500, detail=f"HuggingFace API request failed: {str(e)}")
            except Exception as e:
                logger.error(f"HuggingFace response parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Response parsing failed: {str(e)}")

        elif config["type"] == "openrouter":
            # Check if API key is set
            auth_header = config["headers"].get("Authorization", "")
            if "YOUR_OPENROUTER_KEY" in auth_header:
                raise HTTPException(status_code=400, detail="OpenRouter API key not configured")
            
            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": user_message}],
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            try:
                response = requests.post(
                    config["url"],
                    headers={**config["headers"], "Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    message_content = data["choices"][0].get("message", {}).get("content", "")
                    text = message_content if message_content else "⚠️ No response."
                elif "error" in data:
                    raise HTTPException(status_code=400, detail=f"OpenRouter API error: {data['error']}")
                else:
                    text = "⚠️ No response from OpenRouter."
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"OpenRouter API request failed: {e}")
                raise HTTPException(status_code=500, detail=f"OpenRouter API request failed: {str(e)}")
            except Exception as e:
                logger.error(f"OpenRouter response parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Response parsing failed: {str(e)}")

        elif config["type"] == "google":
            # Check if API key is set
            api_key = config.get("api_key", "")
            if not api_key or "YOUR_API_KEY" in api_key:
                raise HTTPException(status_code=400, detail="Google API key not configured")
            
            full_url = f"{config['url']}?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": user_message}]
                    }
                ]
            }
            
            try:
                response = requests.post(
                    full_url, 
                    headers=config["headers"], 
                    json=payload, 
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if ("candidates" in data and len(data["candidates"]) > 0 and 
                    "content" in data["candidates"][0] and 
                    "parts" in data["candidates"][0]["content"] and 
                    len(data["candidates"][0]["content"]["parts"]) > 0):
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                elif "error" in data:
                    raise HTTPException(status_code=400, detail=f"Google API error: {data['error']}")
                else:
                    logger.error(f"Invalid Google response structure: {data}")
                    text = "⚠️ Invalid response from Google Gemini."
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Google API request failed: {e}")
                raise HTTPException(status_code=500, detail=f"Google API request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Google response parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Response parsing failed: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Unknown model type")

        # Save AI message
        try:
            save_message("ai", text, model_used, session_id)
            logger.info("AI message saved successfully")
        except Exception as e:
            logger.error(f"Failed to save AI message: {e}")
            # Continue and return response even if save fails

        return {"response": text, "model": model_used, "session_id": session_id}

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/chat/history")
def get_chat_history(session_id: str = "default"):
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, message, timestamp 
            FROM chat 
            WHERE session_id = ? 
            ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries for better JSON response
        history = [
            {"role": row[0], "message": row[1], "timestamp": row[2]} 
            for row in rows
        ]
        
        return {"history": history, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@app.delete("/chat/clear")
def clear_chat(session_id: str = Query(...)):
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat WHERE session_id = ?", (session_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {
            "status": "cleared", 
            "session_id": session_id,
            "deleted_messages": deleted_count
        }
    except Exception as e:
        logger.error(f"Error clearing chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat: {str(e)}")

@app.get("/chat/sessions")
def get_all_sessions():
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, MAX(timestamp) as last_time 
            FROM chat 
            GROUP BY session_id 
            ORDER BY last_time DESC
        """)
        sessions = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        sessions_list = [
            {"session_id": row[0], "last_time": row[1]} 
            for row in sessions
        ]
        
        return {"sessions": sessions_list}
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

# Get available models
@app.get("/models")
def get_available_models():
    try:
        models_info = {}
        for model_name, config in MODELS.items():
            # Don't expose API keys in the response
            safe_config = {
                "type": config["type"],
                "name": model_name
            }
            if config["type"] == "openrouter":
                safe_config["model"] = config["model"]
            models_info[model_name] = safe_config
        
        return {"models": models_info}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "FastAPI backend is running"}

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Chat API is running", 
        "endpoints": {
            "chat": "POST /chat",
            "history": "GET /chat/history",
            "clear": "DELETE /chat/clear",
            "sessions": "GET /chat/sessions",
            "models": "GET /models",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)