# MongoDB on Claude Managed Agents

Setup boilerplate for the [**Fraud Review Agent with MongoDB Atlas and Claude Managed Agents**](../CMA_with_mongodb_atlas.ipynb)
cookbook. The **teaching code lives inline in the notebook** — the four retrieval pipeline
builders, the custom-tool handlers, and the `requires_action` gate loop are all defined there.
This package holds only the pieces the notebook imports rather than reads.

| Module | What's inside |
| --- | --- |
| [`config.py`](config.py) | Tunables, index names, and the MongoDB server-version check (`supports_rank_fusion`). |
| [`embeddings.py`](embeddings.py) | An embedding + rerank client that adapts the MongoDB Atlas AI endpoint to the `voyageai` interface, so the cookbook is provider-agnostic. |
| [`tools.py`](tools.py) | MongoDB Atlas setup — seed the collection, create the vector + Atlas Search indexes and wait until they are queryable and synced, preflight — plus the shared decision/audit document shapers used by the notebook's `record_decision` handler and the AP2 module. |
| [`ap2_mandates.py`](ap2_mandates.py) | AP2 (Agent Payments Protocol) mandate signing and verification (ES256 JWTs) — a crypto black box the notebook calls through `verify_mandates` and acts on its verdict. |
| [`seed.py`](seed.py) | Loads the plaintext fixture from [`../example_data/mongodb_on_cma/`](../example_data/mongodb_on_cma/seed_transactions.jsonl). |

The MongoDB credential (`MONGO_URI`) only ever lives on your side of the boundary: `pymongo`
runs in the notebook's host-side handlers, never in the agent context or its sandbox. See the
cookbook for the connection pattern and the end-to-end fraud-review agent.
