"""
Browser Hands — Python Client v4
──────────────────────────────────
Accessibility-first API. This client IS hands, eyes, and ears for people with disabilities.
Розширено 20 маркетинговими режимами та супер-функціями.

  🤲 Motor    — click, drag, key combos, checkboxes, context menu
  👁  Vision  — page text, headings, links, images, forms, tables, ARIA
  👂 Hearing  — media control, caption extraction, volume
  📊 Marketing — 20 режимів аналізу: SEO, competitor, ad copy, leads, prices…
  ⚡ Super    — bulk scrape, watch page, smart fill, pipeline

Usage:
    import asyncio
    from portal.hands_client import HandsClient

    async def main():
        c = HandsClient()
        await c.navigate("https://example.com")

        # 📊 MARKETING MODES
        seo   = await c.seo_audit()
        ctas  = await c.cta_analysis()
        leads = await c.lead_form_scan()

        # ⚡ SUPER FUNCTIONS
        report = await c.extract_all("https://competitor.com")
        data   = await c.bulk_scrape(["https://a.com", "https://b.com"], mode="price_monitor")

    asyncio.run(main())
"""

from __future__ import annotations

from typing import Any

from portal import hands_server as _srv


class HandsClient:
    """High-level browser automation API. All methods are async."""

    # ── Navigation ─────────────────────────────────────────────────────────────

    async def navigate(self, url: str, timeout: float = 25.0) -> dict:
        return await _srv.send_command({"action": "navigate", "url": url}, timeout=timeout)

    async def get_url(self, timeout: float = 5.0) -> str:
        r = await _srv.send_command({"action": "get_url"}, timeout=timeout)
        return r.get("result", {}).get("url", "")

    async def get_title(self, timeout: float = 5.0) -> str:
        r = await _srv.send_command({"action": "get_title"}, timeout=timeout)
        return r.get("result", {}).get("title", "")

    # ── Interaction ─────────────────────────────────────────────────────────────

    async def click(self, selector: str, timeout: float = 10.0) -> dict:
        return await _srv.send_command({"action": "click", "selector": selector}, timeout=timeout)

    async def type(
        self, selector: str, text: str, clear: bool = True, timeout: float = 10.0
    ) -> dict:
        return await _srv.send_command(
            {"action": "type", "selector": selector, "text": text, "clear": clear},
            timeout=timeout,
        )

    async def select(self, selector: str, value: str, timeout: float = 10.0) -> dict:
        return await _srv.send_command(
            {"action": "select", "selector": selector, "value": value}, timeout=timeout
        )

    async def clear(self, selector: str, timeout: float = 10.0) -> dict:
        return await _srv.send_command({"action": "clear", "selector": selector}, timeout=timeout)

    async def hover(self, selector: str, timeout: float = 10.0) -> dict:
        return await _srv.send_command({"action": "hover", "selector": selector}, timeout=timeout)

    async def focus(self, selector: str, timeout: float = 10.0) -> dict:
        return await _srv.send_command({"action": "focus", "selector": selector}, timeout=timeout)

    async def key_press(self, key: str, selector: str | None = None, timeout: float = 10.0) -> dict:
        cmd: dict[str, Any] = {"action": "key_press", "key": key}
        if selector:
            cmd["selector"] = selector
        return await _srv.send_command(cmd, timeout=timeout)

    async def scroll(
        self, selector: str | None = None, x: int = 0, y: int = 400, timeout: float = 5.0
    ) -> dict:
        cmd: dict[str, Any] = {"action": "scroll", "x": x, "y": y}
        if selector:
            cmd["selector"] = selector
        return await _srv.send_command(cmd, timeout=timeout)

    # ── Reading ─────────────────────────────────────────────────────────────────

    async def get_text(self, selector: str, timeout: float = 10.0) -> str:
        r = await _srv.send_command({"action": "get_text", "selector": selector}, timeout=timeout)
        return r.get("result", {}).get("text", "")

    async def get_attr(self, selector: str, attr: str, timeout: float = 10.0) -> str | None:
        r = await _srv.send_command(
            {"action": "get_attr", "selector": selector, "attr": attr}, timeout=timeout
        )
        return r.get("result", {}).get("value")

    async def get_value(self, selector: str, timeout: float = 10.0) -> str | None:
        r = await _srv.send_command({"action": "get_value", "selector": selector}, timeout=timeout)
        return r.get("result", {}).get("value")

    # ── Assertions & waiting ────────────────────────────────────────────────────

    async def wait_for(self, selector: str, timeout: float = 15.0) -> dict:
        return await _srv.send_command(
            {"action": "wait_for", "selector": selector, "timeoutMs": int(timeout * 1000)},
            timeout=timeout + 2,
        )

    async def wait_for_hidden(self, selector: str, timeout: float = 15.0) -> dict:
        return await _srv.send_command(
            {"action": "wait_for_hidden", "selector": selector, "timeoutMs": int(timeout * 1000)},
            timeout=timeout + 2,
        )

    async def assert_(  # noqa: UP005
        self,
        selector: str,
        text: str | None = None,
        contains: str | None = None,
        exists: bool = True,
        timeout: float = 10.0,
    ) -> dict:
        cmd: dict[str, Any] = {"action": "assert", "selector": selector, "exists": exists}
        if text is not None:
            cmd["text"] = text
        if contains is not None:
            cmd["contains"] = contains
        return await _srv.send_command(cmd, timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════
    # 🤲 Motor (hands) — for people without hands
    # ══════════════════════════════════════════════════════════════════════════

    async def double_click(self, selector: str, timeout: float = 10.0) -> dict:
        """Double-click an element (open files, select words, etc.)."""
        return await _srv.send_command(
            {"action": "double_click", "selector": selector}, timeout=timeout
        )

    async def right_click(self, selector: str, timeout: float = 10.0) -> dict:
        """Right-click to open context menu."""
        return await _srv.send_command(
            {"action": "right_click", "selector": selector}, timeout=timeout
        )

    async def drag(
        self,
        from_selector: str | None = None,
        to_selector: str | None = None,
        from_x: int | None = None,
        from_y: int | None = None,
        to_x: int | None = None,
        to_y: int | None = None,
        timeout: float = 10.0,
    ) -> dict:
        """Drag from one element/coordinate to another."""
        cmd: dict[str, Any] = {"action": "drag"}
        if from_selector:
            cmd["fromSelector"] = from_selector
        if to_selector:
            cmd["toSelector"] = to_selector
        if from_x is not None:
            cmd["fromX"] = from_x
        if from_y is not None:
            cmd["fromY"] = from_y
        if to_x is not None:
            cmd["toX"] = to_x
        if to_y is not None:
            cmd["toY"] = to_y
        return await _srv.send_command(cmd, timeout=timeout)

    async def key_combo(self, keys: str, selector: str | None = None, timeout: float = 5.0) -> dict:
        """
        Press a key combination: "Ctrl+C", "Alt+Tab", "Ctrl+Shift+T", "Shift+Enter".
        Supported modifiers: Ctrl, Alt, Shift, Meta/Cmd.
        """
        cmd: dict[str, Any] = {"action": "key_combo", "keys": keys}
        if selector:
            cmd["selector"] = selector
        return await _srv.send_command(cmd, timeout=timeout)

    async def check(self, selector: str, timeout: float = 10.0) -> dict:
        """Check a checkbox or radio button."""
        return await _srv.send_command({"action": "check", "selector": selector}, timeout=timeout)

    async def uncheck(self, selector: str, timeout: float = 10.0) -> dict:
        """Uncheck a checkbox."""
        return await _srv.send_command({"action": "uncheck", "selector": selector}, timeout=timeout)

    async def back(self, timeout: float = 5.0) -> dict:
        """Browser history back."""
        return await _srv.send_command({"action": "back"}, timeout=timeout)

    async def forward(self, timeout: float = 5.0) -> dict:
        """Browser history forward."""
        return await _srv.send_command({"action": "forward"}, timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════
    # 👁  Vision (eyes) — for people without sight
    # ══════════════════════════════════════════════════════════════════════════

    async def get_page_text(self, timeout: float = 5.0) -> str:
        """
        Read entire page as plain text in reading order.
        Headings, links, images (alt) included. Use as: 'read the screen'.
        """
        r = await _srv.send_command({"action": "get_page_text"}, timeout=timeout)
        return r.get("result", {}).get("text", "")

    async def get_headings(self, timeout: float = 5.0) -> list[dict]:
        """
        Page heading structure h1–h6.
        Blind users navigate by headings — this is the table of contents.
        """
        r = await _srv.send_command({"action": "get_headings"}, timeout=timeout)
        return r.get("result", {}).get("headings", [])

    async def get_links(self, visible_only: bool = True, timeout: float = 5.0) -> list[dict]:
        """All links with text + href. Returns [{text, href, title, target}]."""
        r = await _srv.send_command(
            {"action": "get_links", "visibleOnly": visible_only}, timeout=timeout
        )
        return r.get("result", {}).get("links", [])

    async def get_images(self, visible_only: bool = True, timeout: float = 5.0) -> list[dict]:
        """All images with alt text + src. Returns [{alt, src, title, hasAlt}]."""
        r = await _srv.send_command(
            {"action": "get_images", "visibleOnly": visible_only}, timeout=timeout
        )
        return r.get("result", {}).get("images", [])

    async def get_forms(self, timeout: float = 5.0) -> list[dict]:
        """
        All form fields with labels, type, value, errors, required status.
        Use to understand what a form is asking before filling it.
        Returns [{label, type, name, value, required, invalid, error, options}].
        """
        r = await _srv.send_command({"action": "get_forms"}, timeout=timeout)
        return r.get("result", {}).get("fields", [])

    async def get_landmarks(self, timeout: float = 5.0) -> list[dict]:
        """
        ARIA landmark regions: main, nav, search, form, banner, footer…
        Blind users jump between landmarks to navigate the page structure.
        Returns [{role, label, tag, heading}].
        """
        r = await _srv.send_command({"action": "get_landmarks"}, timeout=timeout)
        return r.get("result", {}).get("landmarks", [])

    async def get_focused(self, timeout: float = 5.0) -> dict | None:
        """
        Currently focused element. Use to know 'where am I on the page?'
        Returns {tag, type, id, name, text, value, ariaLabel, role} or None.
        """
        r = await _srv.send_command({"action": "get_focused"}, timeout=timeout)
        return r.get("result", {}).get("focused")

    async def find_all(self, selector: str, limit: int = 50, timeout: float = 5.0) -> list[dict]:
        """
        Find all elements matching selector. Returns [{tag, text, value, id, href}].
        Use to list all menu items, buttons, or options on page.
        """
        r = await _srv.send_command(
            {"action": "find_all", "selector": selector, "limit": limit}, timeout=timeout
        )
        return r.get("result", {}).get("items", [])

    async def get_table(self, selector: str | None = None, timeout: float = 10.0) -> dict:
        """
        Parse a table into structured data: {headers, rows, rowCount, colCount}.
        Blind users need row/column context — this provides it.
        """
        cmd: dict[str, Any] = {"action": "get_table"}
        if selector:
            cmd["selector"] = selector
        r = await _srv.send_command(cmd, timeout=timeout)
        return r.get("result", {})

    async def get_aria_info(self, selector: str | None = None, timeout: float = 5.0) -> dict:
        """
        Full ARIA state of an element: role, name, description, expanded,
        required, invalid, live region, valuenow/min/max, etc.
        """
        cmd: dict[str, Any] = {"action": "get_aria_info"}
        if selector:
            cmd["selector"] = selector
        r = await _srv.send_command(cmd, timeout=timeout)
        return r.get("result", {})

    # ══════════════════════════════════════════════════════════════════════════
    # 👂 Hearing (ears) — for people without hearing
    # ══════════════════════════════════════════════════════════════════════════

    async def get_media(self, timeout: float = 5.0) -> list[dict]:
        """
        Info about all audio/video on the page.
        Returns [{tag, src, duration, paused, muted, volume, tracks, hasCaptions}].
        """
        r = await _srv.send_command({"action": "get_media"}, timeout=timeout)
        return r.get("result", {}).get("media", [])

    async def play_media(self, selector: str | None = None, timeout: float = 5.0) -> dict:
        """Play a video/audio element (first found if no selector)."""
        cmd: dict[str, Any] = {"action": "play_media"}
        if selector:
            cmd["selector"] = selector
        return await _srv.send_command(cmd, timeout=timeout)

    async def pause_media(self, selector: str | None = None, timeout: float = 5.0) -> dict:
        """Pause a video/audio element."""
        cmd: dict[str, Any] = {"action": "pause_media"}
        if selector:
            cmd["selector"] = selector
        return await _srv.send_command(cmd, timeout=timeout)

    async def set_volume(
        self,
        volume: float | None = None,
        mute: bool | None = None,
        selector: str | None = None,
        timeout: float = 5.0,
    ) -> dict:
        """Set media volume (0.0–1.0) and/or mute state."""
        cmd: dict[str, Any] = {"action": "set_volume"}
        if selector is not None:
            cmd["selector"] = selector
        if volume is not None:
            cmd["volume"] = volume
        if mute is not None:
            cmd["mute"] = mute
        return await _srv.send_command(cmd, timeout=timeout)

    async def get_captions(
        self, selector: str | None = None, kind: str = "captions", timeout: float = 10.0
    ) -> dict:
        """
        Extract caption/subtitle text from a video.
        Returns {cues: [{start, end, text}], transcript: str, hasCaptions: bool}.
        kind = "captions" | "subtitles" | "descriptions" | "any"
        Use transcript to 'hear' what was said in the video.
        """
        cmd: dict[str, Any] = {"action": "get_captions", "kind": kind}
        if selector:
            cmd["selector"] = selector
        r = await _srv.send_command(cmd, timeout=timeout)
        return r.get("result", {})

    async def enable_captions(
        self, language: str = "uk", selector: str | None = None, timeout: float = 5.0
    ) -> dict:
        """
        Turn on closed captions on a video.
        Finds best track matching language, then any captions/subtitles.
        """
        cmd: dict[str, Any] = {"action": "enable_captions", "language": language}
        if selector:
            cmd["selector"] = selector
        r = await _srv.send_command(cmd, timeout=timeout)
        return r.get("result", {})

    # ── Utilities ───────────────────────────────────────────────────────────────

    async def screenshot(self, timeout: float = 10.0) -> str:
        """Take a screenshot. Returns base64 PNG data URL."""
        r = await _srv.send_command({"action": "screenshot"}, timeout=timeout)
        return r.get("result", {}).get("dataUrl", "")

    async def eval(self, code: str, timeout: float = 5.0) -> Any:
        """Run a JS expression in a sandboxed Worker. Returns string result."""
        r = await _srv.send_command({"action": "eval", "code": code}, timeout=timeout)
        return r.get("result", {}).get("result")

    # ── Pipeline ────────────────────────────────────────────────────────────────

    async def pipeline(
        self, commands: list[dict[str, Any]], continue_on_error: bool = False, timeout: float = 60.0
    ) -> list[dict]:
        """
        Execute multiple commands in sequence atomically.
        Stops on first failure unless continue_on_error=True.

        Example:
            results = await client.pipeline([
                {"action": "navigate", "url": "https://example.com"},
                {"action": "type",  "selector": "name=email", "text": "u@x.com"},
                {"action": "click", "selector": "text=Login"},
                {"action": "assert", "selector": "testid=dashboard"},
            ])
        """
        return await _srv.send_pipeline(
            commands, timeout=timeout, continue_on_error=continue_on_error
        )

    # ── Log access ──────────────────────────────────────────────────────────────

    async def get_log(self, limit: int = 100) -> list[dict]:
        """Get the extension action log from chrome.storage."""
        return await _srv.get_log(limit=limit)

    async def clear_log(self) -> None:
        """Clear the extension action log."""
        await _srv.clear_log()

    async def get_status(self) -> dict:
        """Return info about the currently active browser tab."""
        return await _srv.get_status()

    # ── Smoke tests ─────────────────────────────────────────────────────────────

    async def smoke_login_form(
        self,
        url: str,
        email_selector: str = "name=email",
        password_selector: str = "name=password",  # noqa: S107
        submit_selector: str = "input[type=submit]",
        email: str = "test@example.com",
        password: str = "",  # noqa: S107 — pass real password at call site
        success_selector: str = "testid=dashboard",
    ) -> bool:
        """
        Smoke test: navigate → type credentials → submit → assert success element.
        Pass real credentials at call site.
        Returns True if all steps pass.
        """
        results = await self.pipeline(
            [
                {"action": "navigate", "url": url},
                {"action": "wait_for", "selector": email_selector, "timeoutMs": 10000},
                {"action": "type", "selector": email_selector, "text": email},
                {"action": "type", "selector": password_selector, "text": password},
                {"action": "click", "selector": submit_selector},
                {
                    "action": "assert",
                    "selector": success_selector,
                    "exists": True,
                    "timeoutMs": 15000,
                },
            ]
        )
        return all(r.get("ok") for r in results)
