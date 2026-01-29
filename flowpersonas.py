
import os
import importlib.util

PERSONA_DIR = "./personas"
AVAILABLE = []

def list_personas():
    print("🧠 可載入的人格模組：")
    for file in os.listdir(PERSONA_DIR):
        if file.endswith(".py"):
            print(" -", file.replace(".py", ""))

def load_persona(module_name):
    path = os.path.join(PERSONA_DIR, f"{module_name}.py")
    if not os.path.exists(path):
        print(f"⚠️ 找不到模組：{module_name}")
        return None
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    print("🌀 FlowAgent 語場人格 CLI 啟動")
    list_personas()
    selected = input("🔍 請輸入要載入的人格模組名：").strip()
    mod = load_persona(selected)
    if not mod:
        return
    print(f"✅ 已載入人格：{selected}")
    print("💬 請開始對話（輸入 exit 結束）")
    while True:
        msg = input("你 > ")
        if msg.lower() in ["exit", "quit"]:
            print(f"🧠 {selected}：結束語場互動。")
            break
        print(mod.respond(msg))

if __name__ == "__main__":
    main()
