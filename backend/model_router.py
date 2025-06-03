# Model Router

# backend/model_router.py

import httpx

async def call_huggingface(model_cfg, message):
    headers = {"Authorization": f"Bearer {model_cfg['token']}"}
    payload = {
        "inputs": message,
        "parameters": {"max_new_tokens": 100}
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(model_cfg["url"], headers=headers, json=payload)
        data = res.json()
    return data[0]["generated_text"] if isinstance(data, list) else str(data)

async def call_openrouter(model_cfg, message):
    headers = {
        "Authorization": f"Bearer {model_cfg['token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_cfg["model"],
        "messages": [{"role": "user", "content": message}],
        "max_tokens": 100
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(model_cfg["url"], headers=headers, json=payload)
        data = res.json()
    return data["choices"][0]["message"]["content"]

async def route_model(model_cfg, message):
    provider = model_cfg.get("provider")
    if provider == "huggingface":
        return await call_huggingface(model_cfg, message)
    elif provider == "openrouter":
        return await call_openrouter(model_cfg, message)
    else:
        return f"Provider '{provider}' is not supported yet."
