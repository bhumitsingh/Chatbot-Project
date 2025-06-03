# Model Configuration

MODELS = {
    "open_llama": {
        "type": "huggingface",
        "url": "https://api-inference.huggingface.co/models/openlm-research/open_llama_3b",
        "headers": {
            "Authorization": "Bearer YOUR_HF_TOKEN"
        }
    },
    "mistral": {
        "type": "openrouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "mistralai/mistral-7b-instruct:free",
        "headers": {
            "Authorization": "Bearer YOUR_OPENROUTER_KEY"
        }
    },
    "deepseek_llama70b": {
        "type": "openrouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "deepseek/deepseek-r1-distill-llama-70b:free",
        "headers": {
            "Authorization": "Bearer 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"
        }
    },
    "gemini_flash": {
        "type": "google",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
        "api_key": "AIzaSyBwjdfDTOGrI8eybflXOyTP3G64t7gQkTU",
        "headers": {
            "Content-Type": "application/json"
        }
    }

}