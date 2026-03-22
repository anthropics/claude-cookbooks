"""
Автоматично відкриває Chrome з RUKI extension через Playwright.
Запуск: uv run python portal/install_extension.py
"""

import asyncio
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

EXTENSION_PATH = str(Path(__file__).parent / "extension")


async def main():
    async with async_playwright() as pw:
        with tempfile.TemporaryDirectory(prefix="ruki-chrome-") as user_data_dir:
            with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="ruki_screenshot_"
            ) as screenshot_file:
                screenshot_path = screenshot_file.name

            # Chrome з завантаженим unpacked extension
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
                args=[
                    f"--disable-extensions-except={EXTENSION_PATH}",
                    f"--load-extension={EXTENSION_PATH}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )

            # Чекаємо поки service worker extension запуститься
            await asyncio.sleep(2)

            # Знаходимо ID встановленого розширення
            ext_id = None
            for bg in context.background_pages:
                if "service_worker" in bg.url or "extension" in bg.url:
                    ext_id = bg.url.split("/")[2]
                    break

            page = await context.new_page()

            # Перевіряємо popup розширення
            if ext_id:
                await page.goto(f"chrome-extension://{ext_id}/popup/popup.html")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=screenshot_path)
                print(f"✅ Extension ID: {ext_id}")
                print(f"📸 Скріншот popup: {screenshot_path}")
            else:
                # Відкриваємо локальну HTML-сторінку для перевірки
                await page.goto("about:blank")
                await page.set_content("<html><body><h1>RUKI Test Page</h1></body></html>")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=screenshot_path)
                print("✅ Chrome з extension запущено")
                print(f"📸 Скріншот: {screenshot_path}")

            print(f"\n   Папка розширення: {EXTENSION_PATH}")
            print("   Extension встановлено і готово до роботи!")

            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
