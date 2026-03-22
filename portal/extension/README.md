# Browser Hands — Chrome/Firefox Extension

Автономне керування браузером через AI Portal (SCANDIDIM).

## Встановлення в Chrome (як unpacked extension)

1. Відкрий `chrome://extensions/`
2. Увімкни **Developer mode** (перемикач вгорі праворуч)
3. Натисни **"Load unpacked"**
4. Вибери папку `portal/extension/` з цього репозиторію
5. Розширення з'явиться в тулбарі — іконка ✋

## Встановлення в Firefox (Temporary Add-on)

1. Відкрий `about:debugging#/runtime/this-firefox`
2. Натисни **"Load Temporary Add-on"**
3. Вибери файл `portal/extension/manifest.json`
4. Розширення активне до перезапуску Firefox

> Firefox MV3 підтримується з Firefox 109+.

## Запуск WebSocket-сервера (з'єднання з порталом)

```bash
# З кореня репо
python -m portal.hands_server
```

Сервер слухає `ws://localhost:8765`. Extension автоматично підключається при старті.

## Використання з Python

```python
import asyncio
from portal.hands_client import HandsClient

async def main():
    client = HandsClient()
    await client.navigate("https://example.com")
    await client.type("name=email", "user@example.com")
    await client.click("text=Увійти")
    await client.assert_("testid=dashboard")

asyncio.run(main())
```

## Ручне керування через popup

Клацни іконку розширення в тулбарі:
- Вибери **action** (click, type, navigate, assert...)
- Введи **selector** і **value**
- Натисни **▶ Виконати**
- Натисни **⚡ Підключити портал** щоб з'єднатись з локальним сервером

## Selector стратегія

| Формат | Приклад | Пріоритет |
|--------|---------|-----------|
| `testid=foo` | `testid=submit-btn` | Найвищий |
| `aria=label` | `aria=Email address` | Високий |
| `name=foo` | `name=email` | Середній |
| `text=Текст` | `text=Увійти` | Середній |
| CSS | `#main .btn` | Fallback |

## Підтримувані дії

| Action | Параметри | Опис |
|--------|-----------|------|
| `navigate` | `url` | Перейти на URL |
| `click` | `selector` | Клік по елементу |
| `type` | `selector`, `text`, `clear?` | Ввести текст |
| `select` | `selector`, `value` | Вибрати з dropdown |
| `assert` | `selector`, `text?`, `exists?` | Перевірити DOM |
| `wait_for` | `selector`, `timeoutMs?` | Чекати появи елемента |
| `get_text` | `selector` | Отримати текст |
| `get_attr` | `selector`, `attr` | Отримати атрибут |
| `scroll` | `selector?`, `x?`, `y?` | Прокрутити |
| `eval` | `code` | Виконати JS вираз |

## Smoke тест

```python
from portal.hands_client import HandsClient
import asyncio

async def test():
    c = HandsClient()
    ok = await c.smoke_login_form(
        url="https://yoursite.com/login",
        email_selector="name=email",
        password_selector="name=password",
        submit_selector="text=Увійти",
        success_selector="testid=dashboard",
    )
    print("Smoke test:", "✓ PASS" if ok else "✗ FAIL")

asyncio.run(test())
```

## Структура файлів

```
extension/
  manifest.json              — MV3 маніфест
  background/
    service_worker.js        — command bus + WS bridge
    action_log.js            — chrome.storage action log
  content/
    RUKI.js                  — runner + selectors + actions
  popup/
    popup.html / .css / .js  — UI панель
  icons/
    icon16/48/128.png
```
