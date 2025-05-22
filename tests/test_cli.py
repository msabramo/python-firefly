import os
import tempfile
import pytest
from typer.testing import CliRunner
from unittest import mock
from firefly.cli import app, mock_image
import re

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
        assert "Downloaded image (" in result.output

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

@mock.patch("subprocess.run", side_effect=FileNotFoundError("imgcat not found"))
def test_generate_show_images_imgcat_missing(mock_run):
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
    assert "[warn] Could not display image in terminal using imgcat" in result.output

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

def test_generate_with_all_new_options(monkeypatch):
    # Valid content_class: photo
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--num-variations", "2",
            "--style", '{"presets": ["bw"], "strength": 50}',
            "--structure", '{"strength": 80, "imageReference": {"source": {"uploadId": "abc123"}}}',
            "--prompt-biasing-locale-code", "en-US",
            "--negative-prompt", "no text",
            "--seed", "42",
            "--aspect-ratio", "16:9",
            "--output-format", "jpeg",
            "--content-class", "photo",
            "--use-mocks"
        ]
    )
    assert result.exit_code == 0
    assert "Generated image URL:" in result.output
    # Valid content_class: art
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--content-class", "art",
            "--use-mocks"
        ]
    )
    assert result.exit_code == 0
    assert "Generated image URL:" in result.output
    # Invalid content_class
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--content-class", "invalid",
            "--use-mocks"
        ]
    )
    assert result.exit_code != 0
    assert "content_class must be either 'photo' or 'art'" in result.output

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHF]')
    return ansi_escape.sub('', text)

def test_generate_invalid_json_style(monkeypatch):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--style", "not-a-json",
            "--use-mocks"
        ]
    )
    assert result.exit_code == 2
    assert "Invalid JSON for --style" in strip_ansi(result.output)


def test_generate_invalid_json_structure(monkeypatch):
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--structure", "not-a-json",
            "--use-mocks"
        ]
    )
    assert result.exit_code == 2
    assert "Invalid JSON for --structure" in strip_ansi(result.output)

def test_generate_invalid_num_variations(monkeypatch):
    # Test too low
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--num-variations", "0",
            "--use-mocks"
        ]
    )
    assert result.exit_code == -1
    assert "--num-variations must be between 1 and 4" in result.output
    # Test too high
    result = runner.invoke(
        app,
        [
            "image", "generate",
            "--client-id", "dummy_id",
            "--client-secret", "dummy_secret",
            "--prompt", "test",
            "--num-variations", "5",
            "--use-mocks"
        ]
    )
    assert result.exit_code == -1
    assert "--num-variations must be between 1 and 4" in result.output
