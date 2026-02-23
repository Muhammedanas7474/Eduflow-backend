#!/bin/bash
# Install pgvector via Homebrew
brew install pgvector

# Restart PostgreSQL service to load the extension
brew services restart postgresql@14

# Enable the extension in the database
psql -d eduflow_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
