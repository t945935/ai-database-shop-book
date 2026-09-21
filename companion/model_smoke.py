import os
import psycopg
from semantic_embeddings import ollama_embedding

text = os.environ.get('EMBED_TEXT', '日常咖啡豆，適合手沖。')
vector = ollama_embedding(text)
if len(vector) != 768:
    raise SystemExit(f'expected nomic-embed-text 768 dimensions, got {len(vector)}')
dsn = os.environ.get('SHOP_DSN', 'postgresql://postgres:shop@127.0.0.1:55432/shop')
with psycopg.connect(dsn) as c:
    c.execute(open('vector.sql').read())
    literal = '[' + ','.join(str(float(x)) for x in vector) + ']'
    c.execute("INSERT INTO product_document_embedding(document_id,content,embedding) VALUES (1,%s,%s::vector) ON CONFLICT (document_id) DO UPDATE SET content=EXCLUDED.content, embedding=EXCLUDED.embedding", (text, literal))
    print(c.execute("SELECT content FROM product_document_embedding ORDER BY embedding <=> %s::vector LIMIT 1", (literal,)).fetchone()[0])
