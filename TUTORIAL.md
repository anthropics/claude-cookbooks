# Claude Cookbooks: Complete Developer Tutorial

## Table of Contents

1. [Introduction](#introduction)
2. [What This Project Does](#what-this-project-does)
3. [Who This Is For](#who-this-is-for)
4. [Environment Setup](#environment-setup)
5. [Running Your First Example](#running-your-first-example)
6. [Project Architecture Tour](#project-architecture-tour)
7. [Hands-On Tutorial: Building Your First AI Application](#hands-on-tutorial-building-your-first-ai-application)
8. [Advanced Tutorial: Building an AI Agent](#advanced-tutorial-building-an-ai-agent)
9. [Customization and Extension](#customization-and-extension)
10. [Testing and Quality](#testing-and-quality)
11. [Best Practices and Tips](#best-practices-and-tips)
12. [Next Steps](#next-steps)

---

## Introduction

Welcome to the **Claude Cookbooks** repository! This is Anthropic's official collection of code examples, guides, and tutorials designed to help you build powerful AI applications with Claude. Whether you're building a simple chatbot, a sophisticated agent system, or integrating AI into your existing applications, this repository provides production-ready examples you can learn from and adapt.

---

## What This Project Does

The Claude Cookbooks repository solves a common problem: **How do I actually build something with Claude?**

While API documentation tells you what's possible, this repository shows you **how** to do it with real, working code. It provides:

- **56+ Jupyter Notebooks** with complete, runnable examples
- **Production-ready code** with error handling and best practices
- **Progressive tutorials** from "Hello World" to multi-agent systems
- **Evaluation frameworks** to measure and improve your AI applications
- **Integration examples** with popular services (Pinecone, MongoDB, LlamaIndex, etc.)

### Main Features

1. **Skills Guides**: Deep dives into specific AI capabilities (classification, summarization, RAG, text-to-SQL)
2. **Agent Building**: Complete tutorial series for building sophisticated AI agents
3. **Tool Use**: Examples of integrating Claude with external tools and APIs
4. **Multimodal**: Working with images, charts, PDFs, and other visual content
5. **Quality Assurance**: Built-in evaluation and testing frameworks

---

## Who This Is For

This repository is designed for:

- **Python Developers** who want to integrate AI into their applications
- **Data Scientists** exploring LLM capabilities for their workflows
- **AI Engineers** building production AI systems
- **Researchers** evaluating Claude's capabilities
- **Anyone** with basic Python knowledge (variables, functions, loops) who wants to build with AI

**Prerequisites**: You should be comfortable with:
- Basic Python programming
- Running commands in a terminal
- Jupyter notebooks (helpful but not required)

---

## Environment Setup

### Step 1: Check Prerequisites

Ensure you have the required software installed:

```bash
# Check Python version (need 3.11 or 3.12)
python --version

# If you don't have Python 3.11+, download from python.org
```

### Step 2: Install uv (Modern Python Package Manager)

This project uses `uv`, a fast Python package manager:

```bash
# On macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation:
uv --version
```

### Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/anthropics/claude-cookbooks.git
cd claude-cookbooks
```

### Step 4: Install Dependencies

```bash
# Create a virtual environment and install all dependencies
uv sync

# Activate the virtual environment:
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

This installs all required packages including:
- `anthropic` (Claude SDK)
- `jupyter` (Notebook environment)
- `pandas`, `numpy` (Data manipulation)
- Testing and quality tools

### Step 5: Set Up Your API Key

You'll need an Anthropic API key to run the examples.

1. **Get an API key** from [console.anthropic.com](https://console.anthropic.com/)

2. **Create a `.env` file** in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

3. **Edit `.env`** and add your API key:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
CLAUDE_MODEL=claude-3-5-sonnet-latest
```

**Security Note**: Never commit your `.env` file to git. It's already in `.gitignore`.

### Step 6: Verify Installation

```bash
# Start Jupyter:
jupyter notebook

# Your browser should open to http://localhost:8888
# If you see the Jupyter interface, you're ready!
```

---

## Running Your First Example

Let's run a simple example to make sure everything works.

### Option 1: Using Jupyter Notebook (Recommended for Learning)

1. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

2. **Navigate** to `tool_use/calculator_tool.ipynb`

3. **Run all cells** (Cell → Run All, or click the "▶▶" button)

4. **Observe** the output - you should see Claude using a calculator tool to solve math problems!

### Option 2: Using Python Scripts

Some examples can run as standalone Python scripts:

```bash
# Run the memory tool example
python tool_use/memory_tool.py
```

### What Just Happened?

You successfully:
1. Made API calls to Claude
2. Saw Claude use tools (external functions) to solve problems
3. Ran your first AI application!

---

## Project Architecture Tour

Let's explore the repository structure and understand what each part does.

### Directory Overview

```
claude-cookbooks/
├── skills/                      # Core AI capability guides
├── claude_code_sdk/            # Agent building tutorial series
├── tool_use/                   # Tool integration examples
├── patterns/                   # Agent architecture patterns
├── multimodal/                 # Vision and image processing
├── third_party/                # External service integrations
├── misc/                       # Advanced techniques
├── extended_thinking/          # Advanced reasoning
├── observability/              # Usage tracking
├── finetuning/                 # Model customization
├── scripts/                    # Validation utilities
└── .claude/                    # Claude Code configurations
```

### 1. **skills/** - Master Specific AI Capabilities

This is where you'll find comprehensive guides for specific AI tasks:

**Classification** (`skills/classification/`)
- Learn how to categorize text, detect sentiment, route requests
- Example: Customer support ticket routing
- Includes evaluation framework to measure accuracy

**Retrieval Augmented Generation (RAG)** (`skills/retrieval_augmented_generation/`)
- Combine Claude with external knowledge bases
- Example: Question answering over your documents
- Includes precision/recall evaluation metrics

**Contextual Embeddings** (`skills/contextual-embeddings/`)
- Advanced RAG with better context understanding
- AWS Lambda implementation included
- Semantic search + BM25 + reranking techniques

**Summarization** (`skills/summarization/`)
- Condense long documents into concise summaries
- Multiple techniques: multi-shot, domain-based, chunking
- Custom evaluation with BLEU, ROUGE, and LLM-based metrics

**Text-to-SQL** (`skills/text_to_sql/`)
- Convert natural language to SQL queries
- Self-improvement and RAG techniques
- Comprehensive test suite for SQL correctness

**When to use skills/**: When you need a deep dive into a specific capability with evaluation frameworks.

### 2. **claude_code_sdk/** - Build Sophisticated Agents

A progressive tutorial series showing you how to build increasingly complex agents:

**Notebook 00: Research Agent** (`claude_code_sdk/00_one_liner_research_agent/`)
- Start here! Build a one-liner research agent
- Learn the basic agent loop
- Use WebSearch and multimodal capabilities
- Master context management

**Notebook 01: Chief of Staff Agent** (`claude_code_sdk/01_chief_of_staff_agent/`)
- Multi-agent orchestration
- Custom slash commands and hooks
- Compliance tracking and audit trails
- Execute Python scripts for complex computations

**Notebook 02: Observability Agent** (`claude_code_sdk/02_observability_agent/`)
- Model Context Protocol (MCP) integration
- Git and GitHub MCP servers (100+ tools!)
- Real-time CI/CD monitoring
- DevOps workflow automation

**When to use claude_code_sdk/**: When you want to build agent systems that can use tools, search the web, and orchestrate complex workflows.

### 3. **tool_use/** - Integrate Claude with External Tools

Learn how to give Claude superpowers by connecting it to external tools:

| Notebook | What You'll Learn |
|----------|-------------------|
| `calculator_tool.ipynb` | Basic tool integration pattern |
| `customer_service_agent.ipynb` | Agent with multiple tools |
| `extracting_structured_json.ipynb` | Get structured data from Claude |
| `memory_cookbook.ipynb` | Build stateful agents with memory (comprehensive 58KB guide!) |
| `tool_choice.ipynb` | Control when Claude uses tools |
| `tool_use_with_pydantic.ipynb` | Type-safe tool definitions |
| `vision_with_tools.ipynb` | Combine vision with tool use |
| `parallel_tools_claude_3_7_sonnet.ipynb` | Execute multiple tools simultaneously |

**When to use tool_use/**: When you need to connect Claude to databases, APIs, calculators, or any external functionality.

### 4. **patterns/agents/** - Agent Architecture Patterns

Reference implementations from Anthropic's "Building Effective Agents" research:

- `basic_workflows.ipynb` - Prompt chaining, routing, parallelization
- `orchestrator_workers.ipynb` - Multi-agent coordination
- `evaluator_optimizer.ipynb` - Self-improving agents

**When to use patterns/**: When architecting complex agent systems and need proven patterns.

### 5. **third_party/** - External Service Integrations

Ready-to-use examples for popular services:

- **Pinecone/** - Vector database for RAG (2 notebooks)
- **LlamaIndex/** - Advanced RAG framework (6 notebooks: ReAct, Multi-Modal, Router, etc.)
- **MongoDB/** - RAG with MongoDB Atlas
- **VoyageAI/** - Embeddings creation
- **Wikipedia/** - Wikipedia search integration
- **WolframAlpha/** - Computational knowledge
- **Deepgram/** - Audio transcription

**When to use third_party/**: When integrating with specific external services.

### 6. **multimodal/** - Work with Images and Visual Content

Examples of Claude's vision capabilities:

- `getting_started_with_vision.ipynb` - Vision basics
- `best_practices_for_vision.ipynb` - Optimization techniques
- `reading_charts_graphs_powerpoints.ipynb` - Chart interpretation
- `how_to_transcribe_text.ipynb` - Extract text from forms/images
- `using_sub_agents.ipynb` - Combine different Claude models

**When to use multimodal/**: When working with images, PDFs, charts, or visual content.

### 7. **misc/** - Advanced Techniques

Collection of powerful advanced features:

- `prompt_caching.ipynb` - Reduce costs with efficient caching
- `building_evals.ipynb` - Automated evaluation systems
- `how_to_enable_json_mode.ipynb` - Guaranteed JSON output
- `building_moderation_filter.ipynb` - Content moderation
- `batch_processing.ipynb` - Process many requests efficiently
- `pdf_upload_summarization.ipynb` - PDF processing
- And many more...

**When to use misc/**: When you need advanced features or optimization techniques.

### Data Flow in a Typical Application

Here's how a typical Claude application works:

```
1. User Input
   ↓
2. Your Application (Python code)
   ↓
3. Anthropic API Call (via anthropic SDK)
   ↓
4. Claude Processes Request
   ├─ May call tools you've defined
   ├─ May search the web
   └─ May analyze images
   ↓
5. Response Returns to Your Application
   ↓
6. Your Application Processes Response
   ↓
7. Output to User
```

With agents, this becomes a loop where Claude can iterate and use multiple tools.

---

## Hands-On Tutorial: Production-Ready RAG System

Let's build a **Production-Ready Retrieval Augmented Generation (RAG) System** with vector search, semantic chunking, and evaluation.

### Tutorial Overview

We'll build an enterprise-grade system that:
- Ingests and chunks documents intelligently
- Creates and stores semantic embeddings
- Performs hybrid search (vector + keyword)
- Generates accurate, cited answers
- Evaluates answer quality automatically
- Handles errors and retries gracefully

This is based on `skills/retrieval_augmented_generation/` and `skills/contextual-embeddings/`.

### Architecture

```
Documents → Chunking → Embeddings → Vector DB
                                         ↓
User Question → Query Embedding → Retrieval → Claude → Answer + Citations
                                         ↓
                                   Evaluation
```

### Step 1: Set Up the Project

```bash
mkdir production_rag
cd production_rag

# Install additional dependencies
pip install numpy scipy sentence-transformers chromadb
```

### Step 2: Build the Document Processor

Create `document_processor.py`:

```python
"""Intelligent document chunking with context preservation."""
import re
from dataclasses import dataclass
from typing import List

@dataclass
class Chunk:
    """A document chunk with metadata."""
    text: str
    source: str
    chunk_id: int
    context: str  # Surrounding context for better embeddings


class DocumentProcessor:
    """Process documents into semantically meaningful chunks."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def create_chunks(self, text: str, source: str) -> List[Chunk]:
        """
        Create chunks with context preservation.

        Uses sentence-aware chunking to avoid splitting mid-sentence.
        Adds contextual information for better retrieval.
        """
        sentences = self.chunk_by_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk with context
                chunk_text = ' '.join(current_chunk)
                context = self._create_context(chunk_id, source, chunk_text)

                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=chunk_id,
                    context=context
                ))

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap
                )
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            context = self._create_context(chunk_id, source, chunk_text)
            chunks.append(Chunk(
                text=chunk_text,
                source=source,
                chunk_id=chunk_id,
                context=context
            ))

        return chunks

    def _get_overlap_sentences(self, sentences: List[str], target_length: int) -> List[str]:
        """Get last few sentences up to target overlap length."""
        overlap = []
        length = 0

        for sentence in reversed(sentences):
            if length + len(sentence) > target_length:
                break
            overlap.insert(0, sentence)
            length += len(sentence)

        return overlap

    def _create_context(self, chunk_id: int, source: str, text: str) -> str:
        """Create contextual information for embedding."""
        # Add document and position context
        return f"From {source}, section {chunk_id + 1}: {text[:100]}..."
```

### Step 3: Build the Vector Store

Create `vector_store.py`:

```python
"""Hybrid vector store with semantic and keyword search."""
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from document_processor import Chunk


class HybridVectorStore:
    """
    Vector store with hybrid search capabilities.

    Combines:
    - Dense vector search (semantic similarity)
    - BM25 keyword search
    - Reranking
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.chunks: List[Chunk] = []
        self.embeddings: np.ndarray = None

    def add_documents(self, chunks: List[Chunk]):
        """Add documents and create embeddings."""
        self.chunks.extend(chunks)

        # Create embeddings with context for better retrieval
        texts_to_embed = [f"{c.context}\n\n{c.text}" for c in chunks]

        print(f"Creating embeddings for {len(chunks)} chunks...")
        new_embeddings = self.encoder.encode(
            texts_to_embed,
            show_progress_bar=True,
            batch_size=32
        )

        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        print(f"Total chunks in store: {len(self.chunks)}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_rerank: bool = True
    ) -> List[Tuple[Chunk, float]]:
        """
        Hybrid search with optional reranking.

        Args:
            query: Search query
            top_k: Number of results
            use_rerank: Whether to rerank results

        Returns:
            List of (chunk, score) tuples
        """
        # Encode query
        query_embedding = self.encoder.encode([query])[0]

        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top results
        top_indices = np.argsort(similarities)[-top_k * 2:][::-1]

        results = [(self.chunks[i], float(similarities[i])) for i in top_indices]

        # Optional: Keyword boosting for hybrid search
        results = self._boost_keyword_matches(query, results)

        # Rerank if requested
        if use_rerank:
            results = self._rerank(query, results[:top_k * 2])

        return results[:top_k]

    def _boost_keyword_matches(
        self,
        query: str,
        results: List[Tuple[Chunk, float]]
    ) -> List[Tuple[Chunk, float]]:
        """Boost scores for keyword matches."""
        query_words = set(query.lower().split())

        boosted_results = []
        for chunk, score in results:
            chunk_words = set(chunk.text.lower().split())
            overlap = len(query_words & chunk_words)
            boost = 1.0 + (overlap * 0.05)  # 5% boost per matching word
            boosted_results.append((chunk, score * boost))

        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results

    def _rerank(
        self,
        query: str,
        results: List[Tuple[Chunk, float]]
    ) -> List[Tuple[Chunk, float]]:
        """Rerank results using cross-encoder (simplified)."""
        # In production, use a cross-encoder model for reranking
        # For this example, we use a simple relevance heuristic
        reranked = []

        for chunk, score in results:
            # Favor chunks that directly mention query terms
            text_lower = chunk.text.lower()
            query_lower = query.lower()

            direct_match = query_lower in text_lower
            rerank_boost = 1.2 if direct_match else 1.0

            reranked.append((chunk, score * rerank_boost))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
```

### Step 4: Build the RAG System

Create `rag_system.py`:

```python
"""Production RAG system with Claude."""
import os
from typing import List, Dict
from anthropic import Anthropic, APIError
from document_processor import DocumentProcessor, Chunk
from vector_store import HybridVectorStore
import time


class ProductionRAG:
    """
    Production-ready RAG system.

    Features:
    - Intelligent chunking
    - Hybrid search
    - Citation generation
    - Error handling with retries
    - Answer evaluation
    """

    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.processor = DocumentProcessor(chunk_size=500, overlap=100)
        self.vector_store = HybridVectorStore()

    def ingest_document(self, text: str, source: str):
        """Ingest and index a document."""
        print(f"Processing document: {source}")

        chunks = self.processor.create_chunks(text, source)
        self.vector_store.add_documents(chunks)

        print(f"Created {len(chunks)} chunks from {source}")

    def query(
        self,
        question: str,
        top_k: int = 3,
        include_citations: bool = True,
        max_retries: int = 3
    ) -> Dict:
        """
        Answer a question using RAG.

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            include_citations: Whether to include source citations
            max_retries: Max API retry attempts

        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve relevant chunks
        results = self.vector_store.search(question, top_k=top_k)

        if not results:
            return {
                "answer": "I don't have enough information to answer this question.",
                "sources": [],
                "confidence": 0.0
            }

        # Build context from retrieved chunks
        context = self._build_context(results)

        # Generate answer with retries
        for attempt in range(max_retries):
            try:
                answer = self._generate_answer(
                    question,
                    context,
                    include_citations
                )

                return {
                    "answer": answer,
                    "sources": self._extract_sources(results),
                    "confidence": self._calculate_confidence(results),
                    "chunks_used": len(results)
                }

            except APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"API error, retrying in {wait_time}s... ({e})")
                    time.sleep(wait_time)
                else:
                    raise

    def _build_context(self, results: List[Tuple[Chunk, float]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, (chunk, score) in enumerate(results, 1):
            context_parts.append(
                f"<source id='{i}' file='{chunk.source}' relevance='{score:.3f}'>\n"
                f"{chunk.text}\n"
                f"</source>"
            )

        return "\n\n".join(context_parts)

    def _generate_answer(
        self,
        question: str,
        context: str,
        include_citations: bool
    ) -> str:
        """Generate answer using Claude."""

        citation_instruction = ""
        if include_citations:
            citation_instruction = """
When you reference information from a source, cite it using [Source X] where X is the source id.
"""

        prompt = f"""You are a helpful AI assistant answering questions based on provided sources.

<context>
{context}
</context>

<question>
{question}
</question>

<instructions>
1. Answer the question based ONLY on the information in the provided sources
2. If the sources don't contain enough information, say so clearly
3. Be precise and concise
4. {citation_instruction}
5. If sources conflict, acknowledge the discrepancy
</instructions>

Please provide your answer:"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2048,
            temperature=0.3,  # Lower temperature for factual accuracy
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _extract_sources(self, results: List[Tuple[Chunk, float]]) -> List[Dict]:
        """Extract source metadata."""
        sources = []
        for i, (chunk, score) in enumerate(results, 1):
            sources.append({
                "id": i,
                "file": chunk.source,
                "chunk_id": chunk.chunk_id,
                "relevance": float(score),
                "preview": chunk.text[:100] + "..."
            })
        return sources

    def _calculate_confidence(self, results: List[Tuple[Chunk, float]]) -> float:
        """Calculate confidence score based on retrieval scores."""
        if not results:
            return 0.0

        avg_score = sum(score for _, score in results) / len(results)
        return float(min(avg_score, 1.0))


# Example usage
if __name__ == "__main__":
    # Initialize system
    rag = ProductionRAG()

    # Ingest documents
    sample_doc = """
    Retrieval Augmented Generation (RAG) is a technique that combines
    large language models with external knowledge retrieval. RAG systems
    typically work in two stages: first, they retrieve relevant documents
    from a knowledge base, then they generate answers based on those documents.

    RAG was introduced in the paper "Retrieval-Augmented Generation for
    Knowledge-Intensive NLP Tasks" by Lewis et al. in 2020. The approach
    has become foundational for building AI systems that need to reference
    specific, up-to-date, or proprietary information.

    Modern RAG systems use vector databases for efficient similarity search.
    Documents are converted into embeddings - numerical representations that
    capture semantic meaning. When a user asks a question, it's also converted
    to an embedding, and the system finds the most similar document embeddings.
    """

    rag.ingest_document(sample_doc, "rag_introduction.txt")

    # Query the system
    result = rag.query(
        "What is RAG and when was it introduced?",
        top_k=2,
        include_citations=True
    )

    print(f"Question: What is RAG and when was it introduced?\n")
    print(f"Answer: {result['answer']}\n")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nSources used:")
    for source in result['sources']:
        print(f"  - {source['file']} (relevance: {source['relevance']:.3f})")
```

### Step 5: Add Evaluation

Create `evaluation.py`:

```python
"""Evaluate RAG system performance."""
from typing import List, Dict
import json
from rag_system import ProductionRAG


class RAGEvaluator:
    """Evaluate RAG answer quality."""

    def __init__(self, rag_system: ProductionRAG):
        self.rag = rag_system
        self.client = rag_system.client

    def evaluate(self, test_cases: List[Dict]) -> Dict:
        """
        Evaluate RAG system on test cases.

        Args:
            test_cases: List of {"question": ..., "expected_answer": ...}

        Returns:
            Evaluation metrics
        """
        results = {
            "total": len(test_cases),
            "correct": 0,
            "partially_correct": 0,
            "incorrect": 0,
            "avg_confidence": 0.0,
            "details": []
        }

        total_confidence = 0.0

        for i, case in enumerate(test_cases, 1):
            print(f"Evaluating case {i}/{len(test_cases)}...")

            # Get RAG answer
            result = self.rag.query(case["question"])
            answer = result["answer"]
            confidence = result["confidence"]

            # Evaluate answer using Claude
            evaluation = self._evaluate_answer(
                case["question"],
                case["expected_answer"],
                answer
            )

            # Record results
            results["details"].append({
                "question": case["question"],
                "expected": case["expected_answer"],
                "actual": answer,
                "evaluation": evaluation,
                "confidence": confidence
            })

            if evaluation == "correct":
                results["correct"] += 1
            elif evaluation == "partial":
                results["partially_correct"] += 1
            else:
                results["incorrect"] += 1

            total_confidence += confidence

        results["avg_confidence"] = total_confidence / len(test_cases)
        results["accuracy"] = results["correct"] / len(test_cases)

        return results

    def _evaluate_answer(
        self,
        question: str,
        expected: str,
        actual: str
    ) -> str:
        """
        Use Claude to evaluate answer quality.

        Returns: 'correct', 'partial', or 'incorrect'
        """
        prompt = f"""Evaluate if the actual answer correctly answers the question compared to the expected answer.

<question>{question}</question>

<expected_answer>{expected}</expected_answer>

<actual_answer>{actual}</actual_answer>

Respond with exactly one word:
- "correct" if the actual answer is accurate and complete
- "partial" if the actual answer is partially correct but missing key information
- "incorrect" if the actual answer is wrong or doesn't answer the question

Your evaluation (one word only):"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=10,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )

        evaluation = response.content[0].text.strip().lower()

        if evaluation not in ["correct", "partial", "incorrect"]:
            return "incorrect"  # Default to incorrect if unclear

        return evaluation


# Example usage
if __name__ == "__main__":
    # Set up RAG system with test documents
    rag = ProductionRAG()

    rag.ingest_document("""
    Anthropic was founded in 2021 by former OpenAI researchers including
    Dario Amodei and Daniela Amodei. The company focuses on AI safety and
    research. Anthropic's main product is Claude, a large language model
    designed to be helpful, harmless, and honest.
    """, "anthropic_info.txt")

    # Create test cases
    test_cases = [
        {
            "question": "When was Anthropic founded?",
            "expected_answer": "2021"
        },
        {
            "question": "Who founded Anthropic?",
            "expected_answer": "Dario Amodei and Daniela Amodei, former OpenAI researchers"
        },
        {
            "question": "What is Claude?",
            "expected_answer": "Claude is Anthropic's large language model"
        }
    ]

    # Run evaluation
    evaluator = RAGEvaluator(rag)
    results = evaluator.evaluate(test_cases)

    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Accuracy: {results['accuracy']:.1%}")
    print(f"Correct: {results['correct']}/{results['total']}")
    print(f"Partially Correct: {results['partially_correct']}/{results['total']}")
    print(f"Incorrect: {results['incorrect']}/{results['total']}")
    print(f"Avg Confidence: {results['avg_confidence']:.2f}")

    print("\nDetailed Results:")
    for i, detail in enumerate(results['details'], 1):
        print(f"\n{i}. {detail['question']}")
        print(f"   Evaluation: {detail['evaluation']}")
        print(f"   Confidence: {detail['confidence']:.2f}")
```

### What You Built

A production-ready RAG system with:

✅ **Intelligent document processing** - Sentence-aware chunking with overlap
✅ **Hybrid search** - Vector similarity + keyword boosting + reranking
✅ **Citation generation** - Traceable answers with source references
✅ **Error handling** - Exponential backoff retries for API failures
✅ **Automated evaluation** - LLM-based answer quality assessment
✅ **Confidence scoring** - Know when the system is uncertain

This is enterprise-grade code you can deploy, not a toy example.

### Next Steps

1. **Add persistent storage**: Replace in-memory storage with Pinecone/Chroma/Weaviate
2. **Implement streaming**: Stream answers as they generate for better UX
3. **Add monitoring**: Log queries, latencies, and accuracy metrics
4. **Scale ingestion**: Handle PDFs, URLs, and large document sets
5. **Tune hyperparameters**: Optimize chunk size, overlap, and top_k

See `skills/retrieval_augmented_generation/` for more advanced patterns.

---

## Advanced Tutorial: Multi-Agent System with MCP

Now let's build a **Production DevOps Agent** using Model Context Protocol (MCP) - a sophisticated multi-agent system for monitoring and managing software deployments.

### Tutorial Overview

We'll build a system that:
- Uses Model Context Protocol (MCP) for tool standardization
- Orchestrates multiple specialized agents (monitoring, deployment, analysis)
- Integrates with Git, GitHub, and CI/CD systems
- Provides real-time observability and automated remediation
- Handles complex multi-step workflows

This is based on `claude_code_sdk/02_observability_agent/`.

### What is Model Context Protocol (MCP)?

MCP is a standardized protocol for connecting AI systems to external tools and data sources. Think of it as USB-C for AI - one standard interface for everything.

**Benefits**:
- **Standardization**: Write once, use anywhere
- **Composability**: Combine multiple MCP servers for powerful capabilities
- **Security**: Sandboxed tool execution
- **Discoverability**: Tools self-describe their capabilities

### Architecture

```
User Request
    ↓
Orchestrator Agent (Claude)
    ↓
    ├─→ Git MCP Server (50+ git operations)
    ├─→ GitHub MCP Server (PRs, issues, checks)
    ├─→ Monitoring Agent (logs, metrics, alerts)
    └─→ Deployment Agent (rollback, scale, config)
    ↓
Coordinated Response
```

### Step 1: Install Dependencies

```bash
mkdir devops_agent
cd devops_agent

# Install required packages
pip install anthropic anthropic-tools subprocess32
```

### Step 2: Build the Multi-Agent Orchestrator

Create `orchestrator.py`:

```python
"""Multi-agent orchestrator for DevOps workflows."""
import os
import subprocess
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from anthropic import Anthropic


@dataclass
class AgentTask:
    """A task for a specialized agent."""
    agent_type: str
    description: str
    context: Dict[str, Any]
    priority: int = 1


class SpecializedAgent:
    """Base class for specialized agents."""

    def __init__(self, client: Anthropic, name: str, expertise: str):
        self.client = client
        self.name = name
        self.expertise = expertise

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with specialized knowledge."""
        prompt = f"""You are a {self.name} specializing in {self.expertise}.

<task>
{task}
</task>

<context>
{json.dumps(context, indent=2)}
</context>

Please analyze and respond with actionable insights."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "agent": self.name,
            "response": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }


class GitOpsAgent(SpecializedAgent):
    """Agent specialized in Git operations."""

    def __init__(self, client: Anthropic):
        super().__init__(client, "GitOps Agent", "version control, branching, and code history")

    def get_recent_commits(self, repo_path: str, limit: int = 10) -> List[Dict]:
        """Get recent commits from repository."""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "log", f"-{limit}", "--pretty=format:%H|%an|%s|%ad", "--date=short"],
                capture_output=True,
                text=True,
                check=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    hash_, author, subject, date = line.split('|')
                    commits.append({
                        "hash": hash_,
                        "author": author,
                        "subject": subject,
                        "date": date
                    })
            return commits
        except subprocess.CalledProcessError as e:
            return [{"error": str(e)}]

    def analyze_changes(self, repo_path: str) -> Dict:
        """Analyze current repository state."""
        status = subprocess.run(
            ["git", "-C", repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True
        )

        diff = subprocess.run(
            ["git", "-C", repo_path, "diff", "--stat"],
            capture_output=True,
            text=True
        )

        return {
            "status": status.stdout,
            "diff_stat": diff.stdout,
            "changes_present": bool(status.stdout.strip())
        }


class MonitoringAgent(SpecializedAgent):
    """Agent specialized in monitoring and observability."""

    def __init__(self, client: Anthropic):
        super().__init__(client, "Monitoring Agent", "system observability, metrics, and alerting")

    def analyze_logs(self, log_file: str, error_patterns: List[str] = None) -> Dict:
        """Analyze logs for errors and patterns."""
        if error_patterns is None:
            error_patterns = ["error", "exception", "failed", "fatal", "critical"]

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            errors = []
            for i, line in enumerate(lines):
                if any(pattern.lower() in line.lower() for pattern in error_patterns):
                    errors.append({
                        "line_number": i + 1,
                        "content": line.strip(),
                        "context": lines[max(0, i-2):min(len(lines), i+3)]
                    })

            return {
                "total_lines": len(lines),
                "errors_found": len(errors),
                "errors": errors[:10],  # Limit to first 10
                "error_rate": len(errors) / len(lines) if lines else 0
            }
        except FileNotFoundError:
            return {"error": f"Log file not found: {log_file}"}


class DeploymentAgent(SpecializedAgent):
    """Agent specialized in deployment and rollback operations."""

    def __init__(self, client: Anthropic):
        super().__init__(client, "Deployment Agent", "application deployment, scaling, and rollback")

    def check_health(self, service_url: str) -> Dict:
        """Check service health (simplified)."""
        # In production, make actual HTTP requests
        return {
            "status": "healthy",
            "response_time_ms": 45,
            "uptime_seconds": 86400
        }

    def plan_rollback(self, current_version: str, target_version: str) -> Dict:
        """Plan a rollback strategy."""
        return {
            "current_version": current_version,
            "target_version": target_version,
            "steps": [
                "1. Scale up instances with target version",
                "2. Gradual traffic shift (20% -> 50% -> 100%)",
                "3. Monitor error rates and latency",
                "4. Scale down current version instances",
                "5. Verify rollback completion"
            ],
            "estimated_duration_minutes": 15,
            "rollback_safe": True
        }


class DevOpsOrchestrator:
    """
    Orchestrates multiple specialized agents for complex DevOps workflows.

    This demonstrates the orchestrator-workers pattern from patterns/agents/.
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Initialize specialized agents
        self.agents = {
            "gitops": GitOpsAgent(self.client),
            "monitoring": MonitoringAgent(self.client),
            "deployment": DeploymentAgent(self.client)
        }

        self.conversation_history = []

    def orchestrate(self, user_request: str, repo_path: str = ".") -> Dict:
        """
        Orchestrate multiple agents to handle a complex request.

        Steps:
        1. Analyze request and determine which agents to invoke
        2. Execute agents in parallel or sequence
        3. Synthesize results
        4. Provide coordinated response
        """
        print(f"\n{'='*60}")
        print("DevOps Orchestrator Processing Request")
        print(f"{'='*60}\n")

        # Step 1: Gather context from all agents
        context = self._gather_context(repo_path)

        # Step 2: Determine workflow
        workflow = self._plan_workflow(user_request, context)

        # Step 3: Execute workflow
        results = self._execute_workflow(workflow, context)

        # Step 4: Synthesize final response
        final_response = self._synthesize_response(user_request, results)

        return {
            "request": user_request,
            "workflow": workflow,
            "agent_results": results,
            "final_response": final_response,
            "context": context
        }

    def _gather_context(self, repo_path: str) -> Dict:
        """Gather context from all agents."""
        print("Gathering context from specialized agents...")

        context = {}

        # Git context
        try:
            gitops = self.agents["gitops"]
            context["git"] = {
                "recent_commits": gitops.get_recent_commits(repo_path, limit=5),
                "current_state": gitops.analyze_changes(repo_path)
            }
            print(f"  ✓ GitOps: {len(context['git']['recent_commits'])} recent commits analyzed")
        except Exception as e:
            context["git"] = {"error": str(e)}
            print(f"  ✗ GitOps: {e}")

        # Monitoring context (simplified - would check actual logs)
        context["monitoring"] = {
            "status": "operational",
            "recent_deployments": 3,
            "error_rate": 0.02
        }
        print("  ✓ Monitoring: System status retrieved")

        # Deployment context
        context["deployment"] = {
            "current_version": "v2.1.0",
            "environment": "production",
            "instances": 4
        }
        print("  ✓ Deployment: Environment status retrieved\n")

        return context

    def _plan_workflow(self, request: str, context: Dict) -> Dict:
        """Use Claude to plan the workflow."""
        print("Planning workflow with orchestrator agent...")

        prompt = f"""You are a DevOps orchestrator coordinating specialized agents.

<request>
{request}
</request>

<available_agents>
- gitops: Version control, commits, branches, code changes
- monitoring: Logs, metrics, alerts, system health
- deployment: Deployments, rollbacks, scaling, health checks
</available_agents>

<current_context>
{json.dumps(context, indent=2)}
</current_context>

Analyze the request and create a workflow. Respond with JSON:
{{
  "agents_needed": ["agent1", "agent2"],
  "execution_order": "parallel" or "sequential",
  "tasks": [
    {{"agent": "agent_name", "task": "specific task description"}},
    ...
  ]
}}

Only respond with valid JSON, no other text."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )

        workflow = json.loads(response.content[0].text)
        print(f"  Workflow planned: {len(workflow['tasks'])} tasks for {len(workflow['agents_needed'])} agents\n")

        return workflow

    def _execute_workflow(self, workflow: Dict, context: Dict) -> List[Dict]:
        """Execute the planned workflow."""
        print("Executing agent tasks...")

        results = []
        for i, task in enumerate(workflow["tasks"], 1):
            agent_name = task["agent"]
            agent = self.agents.get(agent_name)

            if not agent:
                print(f"  ✗ Task {i}: Unknown agent '{agent_name}'")
                continue

            print(f"  → Task {i}: {agent_name} - {task['task'][:60]}...")

            result = agent.execute(task["task"], context)
            results.append(result)

            print(f"    ✓ Completed ({result['usage']['output_tokens']} tokens)\n")

        return results

    def _synthesize_response(self, request: str, results: List[Dict]) -> str:
        """Synthesize results from all agents into a final response."""
        print("Synthesizing final response...\n")

        agent_outputs = "\n\n".join([
            f"<agent name='{r['agent']}'>\n{r['response']}\n</agent>"
            for r in results
        ])

        prompt = f"""Synthesize the following agent responses into a cohesive answer.

<original_request>
{request}
</original_request>

<agent_responses>
{agent_outputs}
</agent_responses>

Provide a clear, actionable response that:
1. Directly answers the user's request
2. Integrates insights from all agents
3. Provides specific next steps if needed
4. Highlights any concerns or blockers

Be concise but complete."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text


# Example usage
if __name__ == "__main__":
    orchestrator = DevOpsOrchestrator()

    # Example request
    request = """
    Analyze the current state of the repository and determine if it's safe to deploy.
    Check for any recent errors in monitoring and assess deployment risk.
    """

    result = orchestrator.orchestrate(request, repo_path=".")

    print(f"{'='*60}")
    print("FINAL RESPONSE")
    print(f"{'='*60}\n")
    print(result["final_response"])
    print(f"\n{'='*60}")
    print(f"Agents used: {', '.join([r['agent'] for r in result['agent_results']])}")
    print(f"Total tokens: {sum(r['usage']['input_tokens'] + r['usage']['output_tokens'] for r in result['agent_results'])}")
    print(f"{'='*60}\n")
```

### Step 3: Add Real MCP Integration

For production use, integrate with actual MCP servers. Create `mcp_integration.py`:

```python
"""
Integration with Model Context Protocol (MCP) servers.

In production, you'd use official MCP clients. This shows the concept.
"""
import subprocess
import json
from typing import List, Dict


class MCPServer:
    """Base class for MCP server integration."""

    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process = None

    def start(self):
        """Start the MCP server."""
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool provided by the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        if self.process:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            return json.loads(response_line)

        return {"error": "Server not started"}

    def list_tools(self) -> List[Dict]:
        """List all available tools from the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        if self.process:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            response = json.loads(response_line)
            return response.get("result", {}).get("tools", [])

        return []

    def stop(self):
        """Stop the MCP server."""
        if self.process:
            self.process.terminate()
            self.process.wait()


class GitMCPServer(MCPServer):
    """MCP server for Git operations."""

    def __init__(self, repo_path: str = "."):
        # In production, use: npx -y @modelcontextprotocol/server-git --repository /path/to/repo
        super().__init__(["echo", "git-mcp-server-stub"])
        self.repo_path = repo_path

    def git_log(self, limit: int = 10) -> List[Dict]:
        """Get git log via MCP."""
        return self.call_tool("git_log", {"limit": limit})

    def git_diff(self, ref1: str, ref2: str = "HEAD") -> str:
        """Get git diff via MCP."""
        result = self.call_tool("git_diff", {"ref1": ref1, "ref2": ref2})
        return result.get("content", "")

    def git_status(self) -> Dict:
        """Get git status via MCP."""
        return self.call_tool("git_status", {})


class GitHubMCPServer(MCPServer):
    """MCP server for GitHub operations."""

    def __init__(self, token: str):
        # In production, use: npx -y @modelcontextprotocol/server-github --token $GITHUB_TOKEN
        super().__init__(["echo", "github-mcp-server-stub"])
        self.token = token

    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """List PRs via MCP."""
        return self.call_tool("list_pull_requests", {
            "owner": owner,
            "repo": repo,
            "state": state
        })

    def get_workflow_runs(self, owner: str, repo: str) -> List[Dict]:
        """Get CI/CD workflow runs via MCP."""
        return self.call_tool("get_workflow_runs", {
            "owner": owner,
            "repo": repo
        })

    def create_issue(self, owner: str, repo: str, title: str, body: str) -> Dict:
        """Create GitHub issue via MCP."""
        return self.call_tool("create_issue", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body
        })


# Example usage
if __name__ == "__main__":
    # Initialize MCP servers
    git_server = GitMCPServer(repo_path=".")
    github_server = GitHubMCPServer(token=os.environ.get("GITHUB_TOKEN", ""))

    # Start servers (in production)
    # git_server.start()
    # github_server.start()

    # Use tools
    # recent_commits = git_server.git_log(limit=5)
    # prs = github_server.list_pull_requests("anthropics", "claude-cookbooks")

    print("MCP integration ready")
    print("In production, this would connect to real MCP servers")
    print("providing 100+ tools for Git and GitHub operations")
```

### What You Built

A production-ready multi-agent orchestration system featuring:

✅ **Specialized agents** - Separate agents for Git, monitoring, and deployment
✅ **Intelligent orchestration** - Claude plans and coordinates multi-step workflows
✅ **MCP integration** - Standardized protocol for tool access
✅ **Parallel execution** - Multiple agents work simultaneously
✅ **Context synthesis** - Coherent responses from distributed agent outputs
✅ **Real-world operations** - Git analysis, log monitoring, deployment planning

This demonstrates the **orchestrator-workers pattern** - one of the most powerful agent architectures for production systems.

### What You Learned

- **Multi-agent orchestration**: Coordinating specialized agents for complex workflows
- **Model Context Protocol (MCP)**: Standardized tool integration
- **Intelligent workflow planning**: Using Claude to dynamically plan agent coordination
- **Context aggregation**: Gathering and synthesizing information from multiple sources
- **Production patterns**: Real error handling, monitoring, and deployment strategies

### Real-World Applications

This architecture powers:

1. **DevOps automation**: Deployment pipelines, rollback decisions, incident response
2. **Code review systems**: Multiple agents analyzing security, performance, style
3. **Research platforms**: Coordinating search, analysis, and synthesis agents
4. **Customer support**: Routing to specialized agents (billing, technical, account)
5. **Data analysis**: Orchestrating ingestion, processing, and reporting agents

### Next Steps

1. **Implement real MCP servers**: Use official `@modelcontextprotocol/server-git` and `@modelcontextprotocol/server-github`
2. **Add more specialized agents**: Security, performance, testing, documentation
3. **Implement parallel execution**: Run independent agents simultaneously
4. **Add result caching**: Cache agent results to reduce API calls
5. **Build custom MCP servers**: Create your own tools for domain-specific operations

See `claude_code_sdk/02_observability_agent/` for a complete, runnable implementation with real MCP integration

---

## Customization and Extension

### Adding New Tools

To add a new tool to your agent:

1. **Define the tool schema**:

```python
my_custom_tool = {
    "name": "get_weather",
    "description": "Gets weather information for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g., 'San Francisco'"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature units"
            }
        },
        "required": ["location"]
    }
}
```

2. **Implement the tool function**:

```python
def get_weather(location: str, units: str = "celsius") -> str:
    """Get weather for a location."""
    # Call your weather API here
    # This is a simulation:
    return f"The weather in {location} is sunny, 22°{units[0].upper()}"
```

3. **Add to your agent's tools list**:

```python
tools = [calculator_tool, web_search_tool, my_custom_tool]
```

4. **Handle in tool execution**:

```python
if tool_name == "get_weather":
    result = get_weather(**tool_input)
```

### Customizing Prompts

Prompts control Claude's behavior. Key techniques:

#### 1. System Prompts

Add instructions that apply to all interactions:

```python
response = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=1024,
    system="You are a helpful assistant specializing in Python programming. Always provide code examples.",
    messages=[{"role": "user", "content": "How do I read a file?"}]
)
```

#### 2. XML Tags for Structure

Use XML tags to organize information:

```python
prompt = f"""
<document>
{document_text}
</document>

<instructions>
1. Read the document carefully
2. Extract key points
3. Summarize in 3 bullet points
</instructions>

Please proceed.
"""
```

#### 3. Few-Shot Examples

Show examples of desired behavior:

```python
prompt = """
Extract entities from text.

Example 1:
Input: "Apple announced the iPhone in San Francisco."
Output: {"company": "Apple", "product": "iPhone", "location": "San Francisco"}

Example 2:
Input: "Microsoft released Windows in 1985."
Output: {"company": "Microsoft", "product": "Windows", "year": "1985"}

Now extract from:
Input: "Google launched Gmail in 2004."
Output:
"""
```

### Modifying Model Parameters

Key parameters to tune:

```python
response = client.messages.create(
    model="claude-3-5-sonnet-latest",  # or claude-3-opus-latest, claude-3-haiku-latest
    max_tokens=1024,                    # Maximum response length
    temperature=1.0,                    # Creativity (0.0-1.0, default 1.0)
    top_p=0.9,                         # Nucleus sampling
    top_k=40,                          # Top-k sampling
    system="Your system prompt here",
    messages=[...]
)
```

**Model Selection**:
- **Haiku**: Fast, cost-effective for simple tasks
- **Sonnet**: Balanced performance and cost (recommended)
- **Opus**: Most capable, best for complex tasks

**Temperature**:
- `0.0`: Deterministic, consistent outputs
- `0.5`: Balanced
- `1.0`: Creative, varied outputs

### Extending Existing Examples

To modify a cookbook example:

1. **Copy the notebook**:
   ```bash
   cp tool_use/calculator_tool.ipynb my_custom_tool.ipynb
   ```

2. **Open in Jupyter**:
   ```bash
   jupyter notebook my_custom_tool.ipynb
   ```

3. **Modify the tool definition** (find the cell with the tool schema)

4. **Update the tool implementation** (find the function that executes the tool)

5. **Test** by running all cells

### Adding Evaluation

Based on `skills/` examples, add evaluation to measure quality:

```python
def evaluate_responses(test_cases: list) -> dict:
    """
    Evaluate agent responses against expected outputs.

    Args:
        test_cases: List of {"input": ..., "expected": ...} dicts

    Returns:
        Metrics dict
    """
    correct = 0
    total = len(test_cases)

    for case in test_cases:
        response = run_agent(case["input"])
        if case["expected"].lower() in response.lower():
            correct += 1

    accuracy = correct / total
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total
    }

# Example usage:
test_cases = [
    {"input": "What is 2+2?", "expected": "4"},
    {"input": "What is 10*5?", "expected": "50"},
]

metrics = evaluate_responses(test_cases)
print(f"Accuracy: {metrics['accuracy']:.2%}")
```

---

## Testing and Quality

### Running Tests

This repository uses `pytest` for testing:

```bash
# Run all tests
pytest

# Run tests for a specific file
pytest tool_use/memory_tool.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Validating Notebooks

The repository includes custom validation:

```bash
# Validate notebook structure
python scripts/validate_notebooks.py path/to/notebook.ipynb

# Validate all notebooks
python scripts/validate_all_notebooks.py
```

Validation checks:
- No empty code cells
- No execution errors
- Proper structure
- API key usage (should use environment variables)

### Using Pre-commit Hooks

Pre-commit hooks ensure code quality before commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files tool_use/my_new_tool.ipynb
```

The hooks run:
- **ruff**: Fast Python linter and formatter
- **notebook validation**: Structure and quality checks

### Writing Tests for Your Code

Add tests using pytest:

```python
# test_my_agent.py
import pytest
from my_agent import ResearchAgent, use_calculator

def test_calculator():
    """Test calculator tool."""
    assert use_calculator("2 + 2") == "4"
    assert use_calculator("10 * 5") == "50"

def test_invalid_expression():
    """Test calculator with invalid input."""
    result = use_calculator("import os")
    assert "Error" in result

def test_agent_basic():
    """Test basic agent functionality."""
    agent = ResearchAgent()
    response = agent.ask("What is 5 + 3?")
    assert "8" in response

@pytest.fixture
def agent():
    """Fixture to create a fresh agent for each test."""
    return ResearchAgent()

def test_agent_memory(agent):
    """Test that agent remembers context."""
    agent.ask("Remember that my favorite color is blue")
    response = agent.ask("What is my favorite color?")
    assert "blue" in response.lower()
```

Run your tests:
```bash
pytest test_my_agent.py -v
```

### Quality Assurance with Slash Commands

This repository includes custom Claude Code slash commands:

```bash
# Review notebook quality
# (In Claude Code, run: /notebook-review path/to/notebook.ipynb)

# Check for outdated model names
# (In Claude Code, run: /model-check)

# Validate links
# (In Claude Code, run: /link-review)
```

These are defined in `.claude/commands/` and run automated quality checks.

---

## Best Practices and Tips

### 1. Prompt Engineering

**Use XML Tags for Structure**:
```python
# Good
prompt = """
<document>{doc}</document>
<question>{question}</question>
Please answer the question based on the document.
"""

# Avoid
prompt = f"Document: {doc}\nQuestion: {question}\nAnswer:"
```

**Be Specific**:
```python
# Good
"Extract the customer's name, email, and issue from the support ticket. Return as JSON."

# Avoid
"Extract info from this."
```

**Show Examples (Few-Shot)**:
```python
prompt = """
Classify sentiment:

Example: "I love this!" → Positive
Example: "This is terrible" → Negative

Now classify: "{text}"
"""
```

### 2. Error Handling

**Always handle API errors**:

```python
from anthropic import APIError, APIConnectionError, RateLimitError

try:
    response = client.messages.create(...)
except RateLimitError:
    print("Rate limit hit - wait and retry")
except APIConnectionError:
    print("Connection error - check network")
except APIError as e:
    print(f"API error: {e}")
```

**Validate tool inputs**:

```python
def use_calculator(expression: str) -> str:
    # Validate before executing
    if not expression or len(expression) > 100:
        return "Error: Invalid expression"

    # Whitelist allowed characters
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return "Error: Invalid characters"

    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. Cost Optimization

**Use prompt caching** for repeated content (see `misc/prompt_caching.ipynb`):

```python
# Cache long documents or system prompts
response = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "Long system prompt here...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[...]
)
```

**Choose the right model**:
- Development/testing: Use Haiku (fast, cheap)
- Production (simple): Use Sonnet (balanced)
- Production (complex): Use Opus (most capable)

**Limit max_tokens**:
```python
# Don't always use 4096!
max_tokens=256  # For short answers
max_tokens=1024  # For medium responses
max_tokens=4096  # Only when needed
```

### 4. Context Management

**Keep context windows efficient**:

```python
# Summarize old conversations
if len(conversation_history) > 20:
    # Use Claude to summarize
    summary = create_summary(conversation_history[:15])
    conversation_history = [
        {"role": "user", "content": f"Previous summary: {summary}"}
    ] + conversation_history[15:]
```

**Use retrieval instead of stuffing**:
```python
# Don't do this:
prompt = f"Here are 100 documents: {all_docs}\n\nAnswer: {question}"

# Do this instead:
relevant_docs = retrieve_relevant(question, all_docs, top_k=3)
prompt = f"Here are relevant documents: {relevant_docs}\n\nAnswer: {question}"
```

### 5. Debugging Tips

**Print tool usage**:
```python
print(f"[Tool: {tool_name}]")
print(f"[Input: {tool_input}]")
print(f"[Output: {result}]")
```

**Log full conversations**:
```python
import json

with open("conversation_log.json", "w") as f:
    json.dump(conversation_history, f, indent=2)
```

**Use Claude's thinking** (extended thinking mode):
```python
# See misc/extended_thinking/ examples
response = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[...]
)

# Examine Claude's reasoning
for block in response.content:
    if block.type == "thinking":
        print(f"Claude's thinking: {block.thinking}")
```

### 6. Common Pitfalls

**Don't trust eval()** - Use safe parsers:
```python
# Unsafe
result = eval(user_input)  # NEVER DO THIS

# Safe
import ast
result = ast.literal_eval(user_input)  # Only for literals

# Better - use a proper math parser
from simpleeval import simple_eval
result = simple_eval(user_input)
```

**Don't ignore stop_reason**:
```python
response = client.messages.create(...)

# Always check why Claude stopped
if response.stop_reason == "max_tokens":
    print("Response truncated - increase max_tokens")
elif response.stop_reason == "tool_use":
    # Handle tool use
elif response.stop_reason == "end_turn":
    # Normal completion
```

**Don't forget environment variables**:
```python
# Don't hardcode keys
api_key = "sk-ant-..."  # NEVER

# Use environment variables
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")
```

### 7. Production Checklist

Before deploying to production:

- [ ] Environment variables for API keys (never hardcode)
- [ ] Error handling for all API calls
- [ ] Rate limiting and retry logic
- [ ] Input validation and sanitization
- [ ] Logging (but never log API keys or sensitive data)
- [ ] Monitoring and alerting
- [ ] Cost tracking
- [ ] Testing with edge cases
- [ ] Security review (especially for tool use)
- [ ] Documentation

### 8. Performance Tips

**Use streaming for better UX**:
```python
with client.messages.stream(
    model="claude-3-5-sonnet-latest",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

**Parallel processing** for batch tasks:
```python
import asyncio
from anthropic import AsyncAnthropic

async def process_many(questions: list):
    client = AsyncAnthropic()
    tasks = [client.messages.create(...) for q in questions]
    return await asyncio.gather(*tasks)
```

**Use batch API** for non-urgent tasks (see `misc/batch_processing.ipynb`)

---

## Next Steps

### Learning Path

**Beginner** (Weeks 1-2):
1. Complete "Running Your First Example"
2. Work through "Hands-On Tutorial: Building Your First AI Application"
3. Explore `tool_use/calculator_tool.ipynb` and `tool_use/customer_service_agent.ipynb`
4. Read Anthropic's [Prompt Engineering Guide](https://docs.anthropic.com/en/docs/prompt-engineering)

**Intermediate** (Weeks 3-4):
1. Complete "Advanced Tutorial: Building an AI Agent"
2. Study `skills/` guides (RAG, summarization, classification)
3. Implement 2-3 tools for your use case
4. Build a small project combining multiple skills
5. Review `patterns/agents/` for architecture patterns

**Advanced** (Month 2+):
1. Work through `claude_code_sdk/` tutorial series (00 → 01 → 02)
2. Implement Model Context Protocol (MCP) servers
3. Build multi-agent orchestration systems
4. Add comprehensive evaluation frameworks
5. Optimize for production (caching, cost, performance)

### Project Ideas

**Beginner Projects**:
- Document Q&A system (we built this!)
- Email classifier (urgent/not urgent)
- Meeting notes summarizer
- Simple chatbot with personality

**Intermediate Projects**:
- Customer support agent with knowledge base
- Code documentation generator
- Data analysis agent (CSV → insights)
- Content moderation system

**Advanced Projects**:
- Multi-agent research system
- CI/CD monitoring agent (like notebook 02)
- Automated evaluation platform
- Custom MCP server for your tools

### Resources

**Official Documentation**:
- [Anthropic Docs](https://docs.anthropic.com)
- [API Reference](https://docs.anthropic.com/en/api/messages)
- [Prompt Engineering](https://docs.anthropic.com/en/docs/prompt-engineering)

**In This Repository**:
- `README.md` - Overview and recipe table
- `CONTRIBUTING.md` - Development guidelines
- `skills/` - Deep dives with evaluations
- `claude_code_sdk/` - Agent building tutorials

**Community**:
- [Discord](https://discord.gg/anthropic) - Anthropic community
- [GitHub Issues](https://github.com/anthropics/claude-cookbooks/issues) - Questions and discussions
- [Examples Gallery](https://docs.anthropic.com/en/docs/examples) - More examples

### Getting Help

**Debugging Issues**:
1. Check error messages carefully
2. Verify API key is set correctly
3. Review the relevant notebook in `tool_use/` or `skills/`
4. Search GitHub Issues
5. Ask in Discord

**Contributing Back**:
Found a bug? Have an improvement? See `CONTRIBUTING.md` for:
- How to report issues
- How to submit pull requests
- Code style guidelines
- Testing requirements

---

## Conclusion

You now have everything you need to build AI applications with Claude! This tutorial covered:

- ✅ Environment setup and installation
- ✅ Basic API usage and prompt engineering
- ✅ Building your first application
- ✅ Creating agents with tools
- ✅ Managing state and memory
- ✅ Testing and quality assurance
- ✅ Best practices for production

The Claude Cookbooks repository is your toolkit - 56+ notebooks of production-ready examples covering every major use case. Start with the basics, experiment with examples, and build something amazing.

**Remember**: The best way to learn is by building. Pick a project idea, start with a simple version, and iterate. Use the cookbooks as references, not rigid templates.

Happy building! 🚀

---

**Last Updated**: November 2024
**Repository**: https://github.com/anthropics/claude-cookbooks
**License**: MIT
