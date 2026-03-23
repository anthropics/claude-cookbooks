"""
Browser Hands — Multi-Browser Extension Launcher v3
─────────────────────────────────────────────────────
Автоматично знаходить і запускає будь-який Chromium-браузер з RUKI extension.

Підтримувані браузери:
  auto      — автоматичний вибір (Chrome → Edge → Brave → Opera → Vivaldi → Playwright Chromium)
  chrome    — Google Chrome
  edge      — Microsoft Edge
  brave     — Brave Browser
  opera     — Opera
  vivaldi   — Vivaldi
  chromium  — Playwright Chromium (запасний варіант)

Запуск:
  uv run python portal/install_extension.py
  uv run python portal/install_extension.py --browser edge
  uv run python portal/install_extension.py --browser brave --no-headless
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

EXTENSION_PATH = str(Path(__file__).parent / "extension")

# Відомі шляхи до Chromium-браузерів (Linux / macOS / Windows)
_BROWSER_PATHS: dict[str, list[str]] = {
    "chrome": [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/opt/google/chrome/google-chrome",
        "/snap/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        "/usr/bin/microsoft-edge",
        "/usr/bin/microsoft-edge-stable",
        "/usr/bin/microsoft-edge-beta",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "brave": [
        "/usr/bin/brave-browser",
        "/usr/bin/brave-browser-stable",
        "/usr/bin/brave",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "opera": [
        "/usr/bin/opera",
        "/usr/bin/opera-stable",
        "/Applications/Opera.app/Contents/MacOS/Opera",
        r"C:\Users\{user}\AppData\Local\Programs\Opera\launcher.exe",
    ],
    "vivaldi": [
        "/usr/bin/vivaldi",
        "/usr/bin/vivaldi-stable",
        "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi",
        r"C:\Users\{user}\AppData\Local\Vivaldi\Application\vivaldi.exe",
    ],
}

# Порядок автовибору
_AUTO_ORDER = ["chrome", "edge", "brave", "opera", "vivaldi"]


def _find_playwright_chromium() -> str | None:
    """Знаходить Chromium встановлений будь-якою версією Playwright."""
    cache = Path.home() / ".cache" / "ms-playwright"
    if not cache.exists():
        return None
    candidates = sorted(cache.glob("chromium-*/chrome-linux*/chrome"), reverse=True)
    return str(candidates[0]) if candidates else None


def _find_system_browser(name: str) -> str | None:
    """Шукає бінарний файл браузера в PATH та відомих місцях."""
    # Пошук через PATH
    for cmd in (name, f"{name}-stable", f"{name}-browser"):
        found = shutil.which(cmd)
        if found:
            return found
    # Відомі шляхи
    for path in _BROWSER_PATHS.get(name, []):
        if Path(path).is_file():
            return path
    return None


def find_browser(hint: str = "auto") -> tuple[str, str]:
    """
    Повертає (browser_name, executable_path).
    Піднімає RuntimeError якщо нічого не знайдено.
    """
    pw_chromium = _find_playwright_chromium()

    if hint == "auto":
        for name in _AUTO_ORDER:
            path = _find_system_browser(name)
            if path:
                return name, path
        if pw_chromium:
            return "chromium", pw_chromium
        raise RuntimeError(
            "Жодного браузера не знайдено. "
            "Встанови Chrome, Edge або Brave, "
            "або запусти: playwright install chromium"
        )

    if hint == "chromium":
        if pw_chromium:
            return "chromium", pw_chromium
        raise RuntimeError("Playwright Chromium не знайдено. Запусти: playwright install chromium")

    path = _find_system_browser(hint)
    if path:
        return hint, path

    # Fallback на Playwright Chromium
    if pw_chromium:
        print(f"⚠️  {hint} не знайдено в системі — використовую Playwright Chromium")
        return "chromium", pw_chromium

    raise RuntimeError(
        f"Браузер '{hint}' не знайдено. Встанови його або запусти: playwright install chromium"
    )


def list_available_browsers() -> dict[str, str | None]:
    """Повертає словник {browser_name: path_or_None} для всіх браузерів."""
    result: dict[str, str | None] = {}
    for name in _AUTO_ORDER:
        result[name] = _find_system_browser(name)
    result["chromium (playwright)"] = _find_playwright_chromium()
    return result


async def launch_with_extension(
    browser_name: str,
    executable: str,
    headless: bool = True,
) -> tuple[str | None, str]:
    """
    Запускає браузер з RUKI extension.
    Повертає (extension_id, screenshot_path).
    """
    async with async_playwright() as pw:
        with tempfile.TemporaryDirectory(prefix="ruki-profile-") as user_data_dir:
            with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="ruki_screenshot_"
            ) as f:
                screenshot_path = f.name

            context = await pw.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                executable_path=executable,
                args=[
                    f"--disable-extensions-except={EXTENSION_PATH}",
                    f"--load-extension={EXTENSION_PATH}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-timer-throttling",
                ],
            )

            # Чекаємо поки service worker запуститься
            await asyncio.sleep(2)

            # Знаходимо ID розширення через background pages
            ext_id: str | None = None
            for bg in context.background_pages:
                parts = bg.url.split("/")
                if len(parts) >= 3 and "extension" in bg.url:
                    ext_id = parts[2]
                    break

            page = await context.new_page()

            if ext_id:
                await page.goto(f"chrome-extension://{ext_id}/popup/popup.html")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=screenshot_path)
                print(f"✅ Браузер: {browser_name}")
                print(f"✅ Extension ID: {ext_id}")
                print(f"📸 Скріншот popup: {screenshot_path}")
            else:
                await page.goto("about:blank")
                await page.set_content(
                    "<html><body style='font-family:sans-serif;padding:20px'>"
                    "<h1>✋ RUKI Extension</h1>"
                    "<p>Розширення завантажено. Перевір chrome://extensions/</p>"
                    "</body></html>"
                )
                await page.wait_for_timeout(1000)
                await page.screenshot(path=screenshot_path)
                print(f"✅ Браузер: {browser_name}")
                print("⚠️  Extension ID не визначено (service worker ще запускається?)")
                print(f"📸 Скріншот: {screenshot_path}")

            print(f"\n   Розширення: {EXTENSION_PATH}")
            print("   RUKI Extension готове до роботи!")

            await context.close()
            return ext_id, screenshot_path


async def main(browser_hint: str = "auto", headless: bool = True, list_browsers: bool = False):
    if list_browsers:
        print("🌐 Доступні браузери:")
        for name, path in list_available_browsers().items():
            status = f"✅ {path}" if path else "❌ не знайдено"
            print(f"   {name:30} {status}")
        return

    browser_name, executable = find_browser(browser_hint)
    print(f"🌐 Запускаємо {browser_name}...")
    print(f"   Виконуваний файл: {executable}")
    await launch_with_extension(browser_name, executable, headless=headless)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Запустити RUKI extension у будь-якому Chromium-браузері",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--browser",
        default="auto",
        choices=["auto", "chrome", "edge", "brave", "opera", "vivaldi", "chromium"],
        help="Браузер для запуску (default: auto)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Запустити з видимим вікном (потрібен дисплей)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Показати всі доступні браузери та їх шляхи",
    )
    args = parser.parse_args()
    asyncio.run(
        main(
            browser_hint=args.browser,
            headless=not args.no_headless,
            list_browsers=args.list,
        )
    )
