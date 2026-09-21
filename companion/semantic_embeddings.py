"""Real-model embedding adapter; the database stores/searches vectors with pgvector."""
import json
import os
import urllib.request


def ollama_embedding(text, model=None, url=None):
    model = model or os.environ.get('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
    url = (url or os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434')).rstrip('/') + '/api/embed'
    body = json.dumps({'model': model, 'input': text}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read())
    embeddings = data.get('embeddings')
    if not embeddings or not isinstance(embeddings[0], list):
        raise ValueError('embedding model response did not contain embeddings')
    return embeddings[0]
