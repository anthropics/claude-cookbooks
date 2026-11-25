"""AP2 (Agent Payments Protocol) mandate verification — the deterministic gate.

AP2 is an open protocol for verifying agent-initiated payments; this module encapsulates its
details so the cookbook can simply call `tool_verify_mandates(...)` and act on the verdict.
It signs and verifies the ES256 Checkout/Payment Mandate JWTs, checks constraints (amount,
type, expiry), and detects double-spend against stored receipts. The notebook never needs to
read this file to follow the story — `tool_verify_mandates(...)` returns a plain verdict dict.

See the AP2 protocol: https://github.com/google-agentic-commerce/AP2
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import jwt as _jwt

from .tools import _new_id, _now


class MandateVerificationError(ValueError): ...


def build_mandate_content(
    mandate_type, agent_pk, mandate_id, constraints, checkout_mandate_hash=None
) -> dict:
    content: dict = {
        "mandate_type": mandate_type,
        "mandate_id": mandate_id,
        "agent_pk": agent_pk,
        "constraints": dict(constraints),
    }
    if checkout_mandate_hash is not None:
        content["checkout_mandate_hash"] = checkout_mandate_hash
    return content


def sign_mandate_jwt(content, private_key, *, exp_delta=None) -> str:
    now = datetime.now(UTC)
    delta = exp_delta if exp_delta is not None else timedelta(hours=24)
    payload = {
        "sub": content["mandate_type"],
        "iat": int(now.timestamp()),
        "exp": int((now + delta).timestamp()),
        **content,
    }
    return _jwt.encode(payload, private_key, algorithm="ES256")


def verify_mandate_jwt(token, public_key) -> dict:
    try:
        return _jwt.decode(token, public_key, algorithms=["ES256"])
    except _jwt.InvalidTokenError as exc:
        raise MandateVerificationError(str(exc)) from exc


def attach_mandates(coll, transaction_ids, *, agent_pk, ts_private_key) -> dict[str, dict]:
    result: dict[str, dict] = {}
    expiry = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    for txn_id in transaction_ids:
        doc = coll.find_one({"transaction_id": txn_id})
        if doc is None:
            continue
        mandate_id = _new_id("mandate")
        checkout_content = build_mandate_content(
            mandate_type="checkout",
            agent_pk=agent_pk,
            mandate_id=mandate_id,
            constraints={
                "max_amount": doc["amount"] * 1.1,
                "currency": doc.get("currency", "USD"),
                "transaction_type": doc.get("transaction_type", "purchase"),
                "not_after": expiry,
            },
        )
        checkout_jwt = sign_mandate_jwt(checkout_content, ts_private_key)
        checkout_hash = hashlib.sha256(checkout_jwt.encode()).hexdigest()
        payment_content = build_mandate_content(
            mandate_type="payment",
            agent_pk=agent_pk,
            mandate_id=mandate_id,
            constraints={"max_amount": doc["amount"] * 1.1, "currency": doc.get("currency", "USD")},
            checkout_mandate_hash=checkout_hash,
        )
        payment_jwt = sign_mandate_jwt(payment_content, ts_private_key)
        coll.update_one(
            {"transaction_id": txn_id},
            {
                "$set": {
                    "checkout_mandate_jwt": checkout_jwt,
                    "payment_mandate_jwt": payment_jwt,
                    "mandate_id": mandate_id,
                    "agent_pk": agent_pk,
                }
            },
        )
        result[txn_id] = {
            "checkout_mandate_jwt": checkout_jwt,
            "payment_mandate_jwt": payment_jwt,
            "mandate_id": mandate_id,
            "agent_pk": agent_pk,
        }
    return result


def tool_verify_mandates(db, transaction_id, ts_public_key) -> dict:
    errors: list[str] = []
    coll = db["transactions"]
    doc = coll.find_one({"transaction_id": transaction_id})
    if doc is None:
        return {
            "valid": False,
            "constraints_satisfied": False,
            "double_spend_detected": False,
            "agent_pk": None,
            "mandate_id": None,
            "errors": ["transaction_not_found"],
        }
    checkout_jwt = doc.get("checkout_mandate_jwt")
    payment_jwt = doc.get("payment_mandate_jwt")
    if not checkout_jwt or not payment_jwt:
        return {
            "valid": False,
            "constraints_satisfied": False,
            "double_spend_detected": False,
            "agent_pk": doc.get("agent_pk"),
            "mandate_id": doc.get("mandate_id"),
            "errors": ["mandate_missing"],
        }
    checkout_payload: dict | None = None
    try:
        checkout_payload = verify_mandate_jwt(checkout_jwt, ts_public_key)
    except MandateVerificationError:
        errors.append("signature_invalid")
    payment_payload: dict | None = None
    try:
        payment_payload = verify_mandate_jwt(payment_jwt, ts_public_key)
    except MandateVerificationError:
        if "signature_invalid" not in errors:
            errors.append("signature_invalid")
    if checkout_payload is not None and payment_payload is not None:
        expected_hash = hashlib.sha256(checkout_jwt.encode()).hexdigest()
        if payment_payload.get("checkout_mandate_hash", "") != expected_hash:
            errors.append("checkout_hash_mismatch")
    if errors:
        return {
            "valid": False,
            "constraints_satisfied": False,
            "double_spend_detected": False,
            "agent_pk": doc.get("agent_pk"),
            "mandate_id": doc.get("mandate_id"),
            "errors": errors,
        }
    constraints_ok = True
    if checkout_payload:
        c = checkout_payload.get("constraints", {})
        if doc["amount"] > c.get("max_amount", float("inf")):
            errors.append("amount_exceeded")
            constraints_ok = False
        doc_type = doc.get("transaction_type", "")
        c_type = c.get("transaction_type", "")
        if c_type and doc_type != c_type:
            errors.append("type_mismatch")
            constraints_ok = False
        not_after_str = c.get("not_after")
        if not_after_str:
            try:
                if datetime.now(UTC) > datetime.fromisoformat(not_after_str):
                    errors.append("mandate_expired")
                    constraints_ok = False
            except ValueError:
                errors.append("mandate_expired")
                constraints_ok = False
    mandate_id = (checkout_payload or {}).get("mandate_id") or doc.get("mandate_id")
    agent_pk = (checkout_payload or {}).get("agent_pk") or doc.get("agent_pk")
    prior = db["mandate_receipts"].find_one({"mandate_id": mandate_id, "agent_pk": agent_pk})
    return {
        "valid": True,
        "constraints_satisfied": constraints_ok,
        "double_spend_detected": prior is not None,
        "agent_pk": agent_pk,
        "mandate_id": mandate_id,
        "errors": errors,
    }


def store_mandate_receipt(db, mandate_id, agent_pk, checkout_mandate_hash, decision) -> None:
    db["mandate_receipts"].insert_one(
        {
            "mandate_id": mandate_id,
            "agent_pk": agent_pk,
            "checkout_mandate_hash": checkout_mandate_hash,
            "decision": decision,
            "timestamp": _now(),
        }
    )
