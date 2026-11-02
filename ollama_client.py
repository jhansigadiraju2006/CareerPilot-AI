"""Small, time-bounded Ollama client for responsive local chat."""
from config import MODEL

# Keep local chat responsive. If the local model is cold or overloaded, return
# control quickly so services.chat can provide its profile-aware offline answer.
CHAT_TIMEOUT_SECONDS = 2.2


def generate(prompt, system=''):
    try:
        import ollama
        client = ollama.Client(timeout=CHAT_TIMEOUT_SECONDS)
        result = client.generate(
            model=MODEL,
            prompt=prompt,
            system=system,
            stream=False,
            keep_alive='10m',
            options={
                'num_predict': 120,
                'temperature': 0.3,
                'num_ctx': 4096,
            },
        )
        return result.get('response', '').strip(), True
    except Exception:
        # A fast contextual fallback is better than leaving the user waiting.
        return '', False
