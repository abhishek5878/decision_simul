#!/bin/bash
# Set your API keys in the environment or in a .env file (do not commit real keys)
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export FIRECRAWL_API_KEY="${FIRECRAWL_API_KEY:-}"
python3 test_credigo_context_graph.py 2>&1 | tee credigo_test_output.log
