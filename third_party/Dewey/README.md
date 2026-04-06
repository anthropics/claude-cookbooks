# Dewey — Managed RAG Backend

[Dewey](https://meetdewey.com) is a managed document intelligence backend that handles the full RAG pipeline — PDF conversion, section extraction, chunking, embedding, and hybrid retrieval — behind a single REST API.

Use Dewey with Claude to build production document Q&A without assembling infrastructure yourself.

## Notebooks

- **[dewey_rag_pipeline.ipynb](dewey_rag_pipeline.ipynb)** — Upload PDFs, run hybrid BM25 + vector search, navigate document structure with section-aware retrieval, stream a cited agentic research answer powered by Claude, and build a RAG chat loop using the Anthropic SDK.

## Resources

- [Dewey documentation](https://meetdewey.com/docs)
- [Dewey Python SDK](https://pypi.org/project/meetdewey/)
- [Free tier signup](https://meetdewey.com) — no credit card required
