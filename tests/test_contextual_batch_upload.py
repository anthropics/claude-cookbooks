"""Regression tests for the contextual retrieval Lambda's output manifest."""

import logging
import runpy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

LAMBDA = (
    Path(__file__).resolve().parents[1]
    / "capabilities/contextual-embeddings/contextual-rag-lambda-function/lambda_function.py"
)


@pytest.mark.parametrize("uploaded", [True, False])
def test_manifest_requires_successful_upload(uploaded, caplog):
    caplog.set_level(logging.DEBUG)  # Restore the Lambda's root logger level after the test.
    s3 = Mock()
    s3.read_from_s3.return_value = {"fileContents": [{"contentBody": "sample"}]}
    s3.write_output_to_s3.return_value = uploaded
    inference = Mock()
    inference.invoke_model_with_response_stream.return_value = ["context"]
    # The Lambda deployment supplies the AWS SDK. Exercise the handler with local adapters.
    with patch.dict(
        "sys.modules",
        s3_adapter=Mock(S3Adapter=Mock(return_value=s3)),
        inference_adapter=Mock(InferenceAdapter=Mock(return_value=inference)),
    ):
        handler = runpy.run_path(str(LAMBDA))["lambda_handler"]

    event = {"bucketName": "sample", "inputFiles": [{"contentBatches": [{"key": "batch.json"}]}]}
    if uploaded:
        result = handler(event, None)
        assert result["outputFiles"][0]["contentBatches"] == [{"key": "Output/batch.json"}]
    else:
        with pytest.raises(RuntimeError, match=r"Output/batch\.json"):
            handler(event, None)
    s3.write_output_to_s3.assert_called_once()
