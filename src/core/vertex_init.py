"""
Vertex AI / Gemini initialization for Sentinel Finance OS.
Provides a shared Gemini Flash model instance for all agents.
"""
import os
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from src.core.config import settings

# Module-level model instance (lazy-initialized)
_model: GenerativeModel = None

def get_model() -> GenerativeModel:
    """
    Returns a shared Gemini Flash model instance.
    Initializes Vertex AI on first call.
    """
    global _model
    if _model is None:
        try:
            vertexai.init(
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_REGION
            )
            _model = GenerativeModel(
                model_name="gemini-1.5-flash-001",
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            print(f"Vertex AI Gemini Flash initialized for project {settings.GCP_PROJECT_ID}")
        except Exception as e:
            print(f"WARNING: Vertex AI init failed ({e}). LLM features will be disabled.")
            _model = None
    return _model


async def extract_with_gemini(prompt: str, fallback: dict = None) -> dict:
    """
    Calls Gemini Flash with a prompt, returns a parsed dict.
    Falls back to `fallback` dict if model is unavailable.
    """
    import json
    model = get_model()
    if model is None:
        return fallback or {}
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return fallback or {}
