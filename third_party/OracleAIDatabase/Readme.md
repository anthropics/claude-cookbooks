# Claude, LangChain, and Oracle AI Database for RAG and AI Agents

This example shows how to build a Retrieval-Augmented Generation (RAG) workflow with:

- **Claude** for grounded answer generation
- **LangChain-style orchestration patterns** for retrieval and application workflows
- **Oracle AI Database Vector Search** for storing embeddings and retrieving relevant context

If you are looking for a practical starting point for **RAG with Claude**, **LangChain and Oracle AI Database**, or an **AI agent stack** that keeps retrieval close to operational data, this notebook is designed to be easy to read, run, and adapt.

## Why this stack works well

This combination is useful because each component solves a different part of the application problem:

- **Claude** is responsible for reasoning over retrieved context and producing grounded responses
- **LangChain** is useful for chaining retrieval, prompts, tools, and agent logic into a larger application workflow
- **Oracle AI Database** provides vector search alongside relational and operational data, which can simplify RAG system design

For developers building AI-enabled applications, this can be a practical architecture when you want to experiment quickly without immediately introducing separate systems for orchestration, retrieval, and application data.

## Why use Oracle AI Database for RAG

Oracle AI Database is a good fit for RAG and AI agent workflows when you want:

- **Vector search and application data in one place**, rather than splitting context retrieval and operational data across separate stores
- **Fewer infrastructure components**, which can make local development and production deployment easier to reason about
- **A converged data model**, useful for applications that mix structured records, metadata, and semantic search
- **A smoother path from prototype to production**, especially for teams already building on Oracle infrastructure
- **Compatibility with application frameworks such as LangChain**, whether you are building a simple retrieval pipeline or a more complex agent workflow

This is especially relevant when the goal is not just to demo vector search, but to build a real application where retrieval is one part of a larger system.

## What you will learn

By working through the notebook, you will learn how to:

- connect to Oracle AI Database from Python
- generate embeddings for your source content
- store vectors and metadata in Oracle
- run vector similarity search against your indexed content
- pass retrieved context into Claude to improve answer quality
- adapt the same retrieval pattern to LangChain-based chains or agent workflows

## Architecture at a glance

The example follows a simple RAG flow:

1. Load source text
2. Generate embeddings for each chunk
3. Store chunks and vectors in Oracle AI Database
4. Embed the user's query
5. Retrieve the most similar chunks with vector search
6. Send the retrieved context to Claude for grounded generation

In a larger application, the same pattern can sit behind a LangChain chain or agent, where retrieval from Oracle AI Database becomes one step in a broader workflow.

## Prerequisites

You will need:

- **Oracle AI Database** (local Oracle Free or Autonomous Database)
- **Anthropic API key**
- **Python 3.10+**
- Notebook dependencies installed for this example

## Environment variables

Create a local `.env` file in `third_party/OracleAIDatabase/` using the provided example file.

Example values:

```env
ANTHROPIC_API_KEY=
ORACLE_USER=PDBADMIN
ORACLE_PASSWORD=YourPassword
ORACLE_DSN=localhost:1521/FREEPDB1
```

Notes:

- `PDBADMIN` is the default local user shown in this example setup.
- `localhost:1521/FREEPDB1` is appropriate for a local Oracle Free container.
- If you are using Oracle Autonomous Database, use the connection details for your environment instead.

## Files in this example

- `rag_using_oracle_ai_db.ipynb` — the main notebook for the RAG workflow
- `.env example` — sample environment variable configuration
- `docker-compose.yml` — local database setup for a containerized Oracle Free workflow

## How to run

1. Set your `ANTHROPIC_API_KEY` in the local `.env` file.
2. Make sure your Oracle database is available and credentials are correct.
3. Open `rag_using_oracle_ai_db.ipynb`.
4. Run the notebook cells in order.

As you go, the notebook will walk through:

- connecting to Oracle AI Database
- creating or using database objects for vector storage
- embedding content
- querying similar chunks
- generating an answer with Claude using retrieved context

## Expected outcome

At the end of the notebook, you should have a working baseline RAG pipeline where:

- your source content is embedded and stored in Oracle
- user queries retrieve the most relevant context with vector similarity search
- Claude answers using the retrieved context instead of relying only on model memory

## Who this is for

This example is especially useful if you are:

- evaluating Oracle AI Database as the retrieval layer for RAG
- building an internal knowledge assistant, AI agent, or enterprise search workflow
- using Claude for grounded generation and considering LangChain for orchestration
- looking for a simple developer-focused example to adapt quickly

## Next steps

Once the baseline example is working, common extensions include:

- swapping in your own documents or structured knowledge base
- improving chunking and retrieval quality
- adding metadata filters
- evaluating answer quality and retrieval relevance
- integrating the retrieval pipeline into a larger LangChain-based application or agent workflow
- deploying the pattern behind an API or application UI
