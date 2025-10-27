import re

from detect_secrets.plugins.base import BasePlugin
from detect_secrets.core.log import log


class AnthropicSecretsDetector(BasePlugin):
    """Scans for common API keys and credentials in notebooks."""

    log.info("Running Anthropic Secrets Detector")
    secret_type = "API Credentials"  # type: ignore

    denylist = [
        # Anthropic API keys (sk-ant-api03-...)
        re.compile(r"sk-ant-api03-[A-Za-z0-9_-]{95,}"),
        # Other API keys (sk-...)
        re.compile(r"sk-[A-Za-z0-9]{48,}"),
        re.compile(r"pa-[A-Za-z0-9]{48,}"),
        # Generic API key patterns
        re.compile(r'api[_-]?key[\'"\s]*[:=][\'"\s]*[A-Za-z0-9_\-]{20,}', re.IGNORECASE),
        re.compile(r'apikey[\'"\s]*[:=][\'"\s]*[A-Za-z0-9_\-]{20,}', re.IGNORECASE),
    ]
