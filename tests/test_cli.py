import os
import shutil
import tempfile
import pytest
from typer.testing import CliRunner
from unittest import mock
from firefly.cli import app, mock_image

runner = CliRunner()

def test_generate_success_with_mocks(monkeypatch):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "a cat coding",
            "--use-mocks"
        ]
    )
    assert result.exit_code == 0
    assert "Generated image URL:" in result.output
    assert mock_image in result.output

def test_generate_download_image(monkeypatch):
    # Use a temp dir to avoid polluting cwd
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        result = runner.invoke(
            app,
            [
                "image", "generate",
                "--client-id", "dummy_id",
                "--client-secret", "dummy_secret",
                "--prompt", "a cat coding",
                "--use-mocks",
                "--download"
            ]
        )
        assert result.exit_code == 0
        # The file should be downloaded with the correct name
        filename = os.path.basename(mock_image)
        assert os.path.exists(filename)
        with open(filename, "rb") as f:
            content = f.read()
        # Should match the test image
        with open(os.path.join(os.path.dirname(__file__), "images", "cat-coding.png"), "rb") as f:
            expected = f.read()
        assert content == expected
        assert f"Downloaded image (" in result.output

@mock.patch("subprocess.run")
def test_generate_show_images(mock_run):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "a cat coding",
            "--use-mocks",
            "--show-images"
        ]
    )
    assert result.exit_code == 0
    # Should attempt to call subprocess.run for imgcat
    assert mock_run.called
    assert "Generated image URL:" in result.output

@pytest.mark.parametrize("missing,expected", [
    ("--client-id", "client_id must be provided"),
    ("--client-secret", "client_secret must be provided"),
])
def test_generate_missing_required(monkeypatch, missing, expected):
    # Ensure env vars are unset
    monkeypatch.delenv("FIREFLY_CLIENT_ID", raising=False)
    monkeypatch.delenv("FIREFLY_CLIENT_SECRET", raising=False)
    args = [
        "image", "generate",
        "--prompt", "a cat coding",
        "--use-mocks"
    ]
    if missing != "--client-id":
        args.extend(["--client-id", "dummy_id"])
    if missing != "--client-secret":
        args.extend(["--client-secret", "dummy_secret"])
    result = runner.invoke(app, args)
    assert result.exit_code != 0
    assert expected in result.output

def test_generate_json_output(monkeypatch):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "a cat coding",
            "--use-mocks",
            "--format", "json"
        ]
    )
    assert result.exit_code == 0
    # Should look like pretty-printed JSON
    assert '{' in result.output and 'outputs' in result.output 

def test_generate_verbose(monkeypatch):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "a cat coding",
            "--use-mocks",
            "--verbose"
        ]
    )
    assert result.exit_code == 0
    # Should include verbose status messages
    assert "Doing request to" in result.output
    assert "Received HTTP" in result.output
