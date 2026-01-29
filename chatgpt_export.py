import os, json, zipfile
from typing import Dict, Any, List, Tuple

def _find_conversations_json(z: zipfile.ZipFile) -> str:
    # 官方 export 常見檔名：conversations.json
    for name in z.namelist():
        if name.endswith("conversations.json"):
            return name
    raise FileNotFoundError("conversations.json not found in export zip")

def load_export(zip_path: str) -> List[Dict[str, Any]]:
    with zipfile.ZipFile(zip_path, "r") as z:
        target = _find_conversations_json(z)
        raw = z.read(target).decode("utf-8")
        return json.loads(raw)

def iter_messages(conv: Dict[str, Any]) -> List[Tuple[str, str]]:
    # 兼容性：不同 export 版本結構可能不同，盡量抽取 role/content
    out = []
    mapping = conv.get("mapping") or {}
    # mapping is dict of nodes with message content
    for _, node in mapping.items():
        msg = (node or {}).get("message") or {}
        if not msg:
            continue
        author = (msg.get("author") or {}).get("role") or ""
        content = msg.get("content") or {}
        parts = content.get("parts") or []
        text = "\n".join([p for p in parts if isinstance(p, str)]).strip()
        if text:
            out.append((author, text))
    # 依序不一定穩定：這裡只保證可 ingest，索引以 conversation_id 主鍵
    return out

def conversation_title(conv: Dict[str, Any]) -> str:
    return conv.get("title") or ""

def conversation_id(conv: Dict[str, Any]) -> str:
    return conv.get("id") or conv.get("conversation_id") or ""
