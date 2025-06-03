from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from model_config import MODELS
from chat_db import init_db, save_message
import requests
import sqlite3

app = FastAPI()

init_db()

class ChatRequest(BaseModel):
    message: str
    model: str = "open_llama"
    session_id: str = "default"  # Optional client session tracking

@app.post("/chat")
async def chat(req: ChatRequest):
    config = MODELS.get(req.model)
    if not config:
        return {"error": f"Model '{req.model}' not supported."}

    headers = config["headers"]
    url = config["url"]

    user_message = req.message
    model_used = req.model
    session_id = req.session_id

    # Save user message
    save_message("user", user_message, model_used, session_id)

    if config["type"] == "huggingface":
        payload = {
            "inputs": user_message,
            "parameters": {"max_new_tokens": 100}
        }
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        text = data[0]["generated_text"] if isinstance(data, list) else str(data)

    elif config["type"] == "openrouter":
        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }
        response = requests.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload
        )
        try:
            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ No response.")
        except Exception as e:
            return {"error": f"Parsing failed: {e}. Raw: {response.text}"}

    elif config["type"] == "google":
        full_url = f"{url}?key={config['api_key']}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_message}]
                }
            ]
        }
        response = requests.post(full_url, headers=headers, json=payload)
        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return {"error": "Invalid response from Gemini: " + str(data)}
    else:
        return {"error": "Unknown model type"}

    # Save AI message
    save_message("ai", text, model_used, session_id)

    return {"response": text}

# History endpoint
@app.get("/chat/history")
def get_chat_history(session_id: str = "default"):
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
    return {"history": rows}

@app.delete("/chat/clear")
def clear_chat(session_id: str = Query(...)):
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

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

        return {"sessions": sessions}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})