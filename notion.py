# 可跑的最小 stub：不做網路請求（避免未授權/未配置 token 時破壞流程）
# 你要接上正式 Notion API 時，只需要替換 pull_database/pull_page 內部實作。
import os
from typing import Dict, Any, List

def pull_database(database_id: str) -> List[Dict[str, Any]]:
    raise RuntimeError("Notion bridge 未啟用：請提供 NOTION_TOKEN 並實作 API 呼叫（本母體交付先保持安全離線）")

def pull_page(page_id: str) -> Dict[str, Any]:
    raise RuntimeError("Notion bridge 未啟用：請提供 NOTION_TOKEN 並實作 API 呼叫（本母體交付先保持安全離線）")
