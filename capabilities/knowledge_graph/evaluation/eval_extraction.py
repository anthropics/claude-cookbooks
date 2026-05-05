"""Precision/recall scoring for knowledge-graph extraction.

Re-runs the extraction prompt from the guide on the two hand-labeled articles
and reports entity and relation P/R/F1 against data/sample_triples.json.
"""

import json
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import anthropic
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

MODEL = "claude-haiku-4-5"
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia policy rejects requests without an identifying User-Agent
HEADERS = {"User-Agent": "claude-cookbooks/1.0 (https://github.com/anthropics/claude-cookbooks)"}

EntityType = Literal["PERSON", "ORGANIZATION", "LOCATION", "EVENT", "ARTIFACT"]


class Entity(BaseModel):
    name: str
    type: EntityType
    description: str


class Relation(BaseModel):
    source: str
    predicate: str
    target: str


class ExtractedGraph(BaseModel):
    entities: list[Entity]
    relations: list[Relation]


PROMPT = """Extract a knowledge graph from the document below.

<document>
{text}
</document>

Extract only entities that are central to what this document is about — skip \
incidental mentions. Every relation must connect two entities you extracted."""

DATA_DIR = Path(__file__).parent.parent / "data"


def load_alias_map() -> dict[str, str]:
    """Surface-form variants mapped to canonical gold names.

    Without this a predicted "National Aeronautics and Space Administration"
    never matches gold "NASA" and relation recall is artificially low. Shared
    with the notebook so inline and standalone scoring stay in sync.
    """
    with open(DATA_DIR / "alias_map.json", encoding="utf-8") as f:
        return json.load(f)


def fetch_summary(title: str) -> str:
    slug = quote(title.replace(" ", "_"), safe="")
    r = requests.get(WIKI_API + slug, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["extract"]


def extract(client: anthropic.Anthropic, text: str) -> ExtractedGraph:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": PROMPT.format(text=text)}],
        output_format=ExtractedGraph,
    )
    return response.parsed_output


def prf(predicted: set, gold: set) -> tuple[float, float, float]:
    tp = len(predicted & gold)
    p = tp / len(predicted) if predicted else 0.0
    r = tp / len(gold) if gold else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()
    alias_map = load_alias_map()

    def canon(name: str) -> str:
        lower = name.lower().strip()
        return alias_map.get(lower, lower)

    with open(DATA_DIR / "sample_triples.json", encoding="utf-8") as f:
        gold = json.load(f)

    ent_p_sum = ent_r_sum = ent_f_sum = 0.0
    rel_p_sum = rel_r_sum = rel_f_sum = 0.0
    scored = 0

    for title, labels in gold.items():
        try:
            text = fetch_summary(title)
            result = extract(client, text)
        except (requests.RequestException, anthropic.APIError) as e:
            print(f"Skipping {title}: {e}")
            continue
        scored += 1

        pred_ents = {canon(e.name) for e in result.entities}
        gold_ents = {canon(e["name"]) for e in labels["entities"]}
        ep, er, ef = prf(pred_ents, gold_ents)
        ent_p_sum += ep
        ent_r_sum += er
        ent_f_sum += ef

        pred_rels = {(canon(r.source), canon(r.target)) for r in result.relations}
        gold_rels = {(canon(r["source"]), canon(r["target"])) for r in labels["relations"]}
        rp, rr, rf = prf(pred_rels, gold_rels)
        rel_p_sum += rp
        rel_r_sum += rr
        rel_f_sum += rf

        print(f"\n{title}")
        print(f"  entities:  P={ep:.2f}  R={er:.2f}  F1={ef:.2f}")
        print(f"  relations: P={rp:.2f}  R={rr:.2f}  F1={rf:.2f}")
        missed_ents = gold_ents - pred_ents
        if missed_ents:
            print(f"  missed entities: {', '.join(sorted(missed_ents))}")
        missed_rels = gold_rels - pred_rels
        if missed_rels:
            print(f"  missed relations: {len(missed_rels)}")

    if not scored:
        print("No documents scored.")
        return

    print(f"\n{'=' * 50}")
    print(f"Macro-averaged over {scored} documents:")
    print(
        f"  entities:  P={ent_p_sum / scored:.2f}  "
        f"R={ent_r_sum / scored:.2f}  F1={ent_f_sum / scored:.2f}"
    )
    print(
        f"  relations: P={rel_p_sum / scored:.2f}  "
        f"R={rel_r_sum / scored:.2f}  F1={rel_f_sum / scored:.2f}"
    )


if __name__ == "__main__":
    main()
