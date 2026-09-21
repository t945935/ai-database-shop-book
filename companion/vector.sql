CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE product_document_embedding (
    document_id bigint PRIMARY KEY,
    content text NOT NULL,
    embedding vector(768) NOT NULL
);
CREATE INDEX product_document_embedding_cosine_idx
    ON product_document_embedding USING hnsw (embedding vector_cosine_ops);
