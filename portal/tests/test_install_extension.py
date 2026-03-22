"""
Unit + integration tests for portal/install_extension.py

Unit tests: mock Playwright повністю — без реального браузера.
Integration test: запускає справжній Chromium headless.

Run:
    uv run pytest portal/tests/test_install_extension.py -v
    uv run pytest portal/tests/test_install_extension.py -v -m integration
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

EXTENSION_PATH = str(Path(__file__).parent.parent / "extension")


def _make_bg_page(url: str) -> MagicMock:
    page = MagicMock()
    page.url = url
    return page


def _make_context(bg_pages=None):
    """Fake Playwright BrowserContext."""
    ctx = MagicMock()
    ctx.background_pages = bg_pages or []
    ctx.new_page = AsyncMock(return_value=_make_page())
    ctx.close = AsyncMock()
    return ctx


def _make_page():
    page = MagicMock()
    page.goto = AsyncMock()
    page.set_content = AsyncMock()
    page.screenshot = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    return page


# ── unit tests ────────────────────────────────────────────────────────────────


class TestExtensionPath:
    def test_extension_dir_exists(self):
        assert Path(EXTENSION_PATH).is_dir(), f"Папка extension не знайдена: {EXTENSION_PATH}"

    def test_manifest_present(self):
        manifest = Path(EXTENSION_PATH) / "manifest.json"
        assert manifest.is_file(), "manifest.json відсутній"

    def test_manifest_version_3(self):
        import json

        manifest = json.loads((Path(EXTENSION_PATH) / "manifest.json").read_text())
        assert manifest["manifest_version"] == 3

    def test_service_worker_exists(self):
        assert (Path(EXTENSION_PATH) / "background" / "service_worker.js").is_file()

    def test_content_script_exists(self):
        assert (Path(EXTENSION_PATH) / "content" / "RUKI.js").is_file()

    def test_popup_html_exists(self):
        assert (Path(EXTENSION_PATH) / "popup" / "popup.html").is_file()


class TestMainWithExtensionId:
    """Коли background page знайдено — відкриваємо popup extension."""

    @pytest.fixture(autouse=True)
    def setup(self):
        ext_id = "abcdefghijklmnopqrstuvwxyzabcdef"
        bg_url = f"chrome-extension://{ext_id}/background/service_worker.js"
        self.ext_id = ext_id
        self.ctx = _make_context(bg_pages=[_make_bg_page(bg_url)])

    def _run(self):
        from portal.install_extension import main

        with patch("portal.install_extension.async_playwright") as mock_pw_cls:
            mock_pw = MagicMock()
            mock_pw_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_pw_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_pw.chromium.launch_persistent_context = AsyncMock(return_value=self.ctx)
            asyncio.run(main())
        return mock_pw

    def test_opens_popup_url(self):
        self._run()
        page = self.ctx.new_page.return_value
        call_url = page.goto.call_args[0][0]
        assert f"chrome-extension://{self.ext_id}/popup/popup.html" == call_url

    def test_takes_screenshot(self):
        self._run()
        page = self.ctx.new_page.return_value
        page.screenshot.assert_called_once()
        path_arg = page.screenshot.call_args[1]["path"]
        assert path_arg.endswith(".png")

    def test_context_closed(self):
        self._run()
        self.ctx.close.assert_called_once()


class TestMainWithoutExtensionId:
    """Коли background page НЕ знайдено — fallback на about:blank."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.ctx = _make_context(bg_pages=[])  # порожній список

    def _run(self):
        from portal.install_extension import main

        with patch("portal.install_extension.async_playwright") as mock_pw_cls:
            mock_pw = MagicMock()
            mock_pw_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_pw_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_pw.chromium.launch_persistent_context = AsyncMock(return_value=self.ctx)
            asyncio.run(main())

    def test_goes_to_about_blank(self):
        self._run()
        page = self.ctx.new_page.return_value
        page.goto.assert_called_once_with("about:blank")

    def test_sets_content(self):
        self._run()
        page = self.ctx.new_page.return_value
        page.set_content.assert_called_once()
        html = page.set_content.call_args[0][0]
        assert "RUKI" in html

    def test_takes_screenshot(self):
        self._run()
        page = self.ctx.new_page.return_value
        page.screenshot.assert_called_once()

    def test_context_closed(self):
        self._run()
        self.ctx.close.assert_called_once()


class TestTempDirCleanup:
    """Після запуску — тимчасова директорія видаляється."""

    def test_temp_dir_deleted_after_run(self):
        from portal.install_extension import main

        captured_dir = []

        original_tempdir = tempfile.TemporaryDirectory

        class CapturingTempDir(original_tempdir):
            def __enter__(self):
                path = super().__enter__()
                captured_dir.append(path)
                return path

        ctx = _make_context(bg_pages=[])

        with (
            patch("portal.install_extension.async_playwright") as mock_pw_cls,
            patch("portal.install_extension.tempfile.TemporaryDirectory", CapturingTempDir),
        ):
            mock_pw = MagicMock()
            mock_pw_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_pw_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_pw.chromium.launch_persistent_context = AsyncMock(return_value=ctx)
            asyncio.run(main())

        assert captured_dir, "TemporaryDirectory не було створено"
        assert not Path(captured_dir[0]).exists(), "Тимчасова директорія не була видалена"


class TestLaunchArgs:
    """Перевіряємо що Chrome запускається з правильними флагами extension."""

    def test_extension_args_passed(self):
        from portal.install_extension import main

        ctx = _make_context(bg_pages=[])
        launch_calls = []

        async def capture_launch(**kwargs):
            launch_calls.append(kwargs)
            return ctx

        with patch("portal.install_extension.async_playwright") as mock_pw_cls:
            mock_pw = MagicMock()
            mock_pw_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_pw_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_pw.chromium.launch_persistent_context = capture_launch
            asyncio.run(main())

        assert launch_calls, "launch_persistent_context не було викликано"
        args = launch_calls[0]["args"]
        assert any("--load-extension=" in a for a in args), "--load-extension не передано"
        assert any("--disable-extensions-except=" in a for a in args)
        ext_arg = next(a for a in args if "--load-extension=" in a)
        assert ext_arg.endswith("extension"), f"Неправильний шлях extension: {ext_arg}"


# ── integration test ──────────────────────────────────────────────────────────


@pytest.mark.integration
class TestRealChromiumLaunch:
    """Запускає справжній Chromium — потребує встановленого браузера."""

    def test_script_runs_without_error(self, capsys):
        from portal.install_extension import main

        asyncio.run(main())
        out = capsys.readouterr().out
        assert "Extension встановлено і готово до роботи!" in out

    def test_screenshot_file_created(self, tmp_path):
        """Screenshot файл реально створюється на диску."""
        import tempfile as tf

        created_paths = []
        original_named = tf.NamedTemporaryFile

        def capturing_named(*args, **kwargs):
            f = original_named(*args, **kwargs)
            created_paths.append(f.name)
            return f

        with patch("portal.install_extension.tempfile.NamedTemporaryFile", capturing_named):
            from portal.install_extension import main

            asyncio.run(main())

        assert created_paths
        assert Path(created_paths[0]).exists(), "Скріншот не створено на диску"
