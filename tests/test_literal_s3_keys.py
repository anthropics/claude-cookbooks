import importlib.util
from pathlib import Path

import pytest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "capabilities/contextual-embeddings/contextual-rag-lambda-function/s3_adapter.py"
)
spec = importlib.util.spec_from_file_location("contextual_s3_adapter", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("s3://bucket/folder/s3://source", ("bucket", "folder/s3://source")),
        ("bucket/folder/key", ("bucket", "folder/key")),
        ("s3://bucket/key", ("bucket", "key")),
    ],
)
def test_parse_preserves_object_key(path, expected):
    adapter = object.__new__(module.S3Adapter)
    assert adapter.parse_s3_path(path) == expected


@pytest.mark.parametrize("path", ["s3://", "s3:///key", "s3://bucket/", "bucket", "/key"])
def test_empty_bucket_or_key_is_invalid(path):
    adapter = object.__new__(module.S3Adapter)
    with pytest.raises(ValueError, match="Invalid S3 path"):
        adapter.parse_s3_path(path)
