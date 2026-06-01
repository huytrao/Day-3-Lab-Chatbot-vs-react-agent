import os
from functools import lru_cache
from pathlib import Path

try:
    from llama_cpp import Llama
except Exception:
    Llama = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "Phi-3-mini-4k-instruct-q4.gguf"
MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", str(DEFAULT_MODEL_PATH))
_LAST_MODEL_ERROR = ""


def get_model_path() -> str:
    """Return the configured local GGUF model path."""
    configured = Path(MODEL_PATH)
    if configured.is_absolute():
        return str(configured)
    return str(PROJECT_ROOT / configured)


def get_model_status() -> str:
    """Return a short model availability status without raising exceptions."""
    path = Path(get_model_path())
    if _LAST_MODEL_ERROR:
        return f"Local model skipped because loading failed: {_LAST_MODEL_ERROR}. Model path: {path}"
    if Llama is None:
        return f"llama-cpp-python is not available; local model skipped. Expected model: {path}"
    if not path.exists():
        return f"Local model file not found: {path}"
    return f"Local model file found: {path}"


@lru_cache(maxsize=1)
def _load_llama() -> object | None:
    """Load the local GGUF model once, returning None if anything fails."""
    global _LAST_MODEL_ERROR
    if Llama is None:
        _LAST_MODEL_ERROR = "llama-cpp-python is not installed or cannot be imported"
        return None
    path = Path(get_model_path())
    if not path.exists():
        _LAST_MODEL_ERROR = "model file does not exist"
        return None
    try:
        model = Llama(
            model_path=str(path),
            n_ctx=2048,
            n_threads=max(1, (os.cpu_count() or 2) - 1),
            verbose=False,
        )
        _LAST_MODEL_ERROR = ""
        return model
    except Exception as exc:
        _LAST_MODEL_ERROR = str(exc)
        return None


def polish_answer_with_local_model(user_message: str, draft_answer: str) -> str:
    """Optionally rewrite a draft answer with the local Phi-3 model.

    The backend must not depend on the local model. If llama-cpp-python is not
    installed, the model file is missing, or CPU instructions are unsupported,
    this function simply returns `draft_answer`.
    """
    llm = _load_llama()
    if llm is None:
        return draft_answer

    prompt = (
        "<|system|>\n"
        "You are a friendly VinWonders travel assistant. Reply in Vietnamese, "
        "be concise, do not invent official prices, and keep demo ticket prices clearly marked as demo."
        "<|end|>\n"
        "<|user|>\n"
        f"Question: {user_message}\n"
        f"Draft answer: {draft_answer}\n"
        "Rewrite the draft into a helpful final answer for the visitor."
        "<|end|>\n"
        "<|assistant|>"
    )

    try:
        response = llm(
            prompt,
            max_tokens=256,
            temperature=0.2,
            stop=["<|end|>"],
            echo=False,
        )
        text = response["choices"][0]["text"].strip()
        return text or draft_answer
    except Exception:
        return draft_answer
