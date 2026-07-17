"""Production prompts for the financial-document Q&A system under evaluation.

This file is intentionally small and separate: it is the artifact a CI pipeline
watches. A pull request that touches ``prompts.py`` is exactly the kind of change
the eval gate exists to vet, so the GitHub Actions workflow in the notebook
triggers ``run_eval.py`` whenever this file changes.
"""

# The grounded production prompt. The final sentence — decline when the document
# does not contain the answer — is the guardrail the regression gate protects.
PROD_SYSTEM_PROMPT = """\
You are a financial document analyst. Answer the user's question using ONLY the \
information in the provided document.

- Be precise and professional; this is a regulated setting.
- Show brief working for any calculation.
- If the document does not contain the information needed to answer, say clearly \
that it cannot be determined from the document. Never guess or fabricate a value."""
