
import json
import argparse
from pathlib import Path

def mount_personas(folder):
    index = []
    for path in Path(folder).rglob("*.flpkg.json"):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            index.append({
                "name": meta.get("name"),
                "path": str(path),
                "source": meta.get("source"),
                "fx_count": len(meta.get("fx_path", []))
            })
        except Exception:
            continue

    index_path = Path(folder) / "PersonaIndex.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"[✔] Mounted {len(index)} personas → PersonaIndex.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Directory with .flpkg.json files")
    args = parser.parse_args()
    mount_personas(args.dir)
