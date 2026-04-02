-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table to store user intent signals for agentic pruning
CREATE TABLE IF NOT EXISTS user_intent_signals (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    intent_category TEXT NOT NULL, -- e.g., 'travel', 'lifestyle'
    intent_type TEXT NOT NULL, -- 'POSITIVE' or 'NEGATIVE'
    context_text TEXT, -- Raw text of the user intent
    embedding vector(768), -- Vertex AI textembedding-gecko default dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS user_intent_vector_idx ON user_intent_signals USING hnsw (embedding vector_cosine_ops);
