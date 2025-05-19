# stdlib imports
import contextlib
import json
import os
from urllib.parse import urlparse

# third party imports
import requests
import responses
from rich import print_json
import typer

# local imports
from firefly import FireflyClient


app = typer.Typer()


def use_requests_mock():
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()

    ims_url = "https://ims-na1.adobelogin.com/ims/token/v3"
    image_url = "https://firefly-api.adobe.io/v3/images/generate"
    mock_image = "https://clio-assets.adobe.com/clio-playground/image-style-zeros/v3/images/Photo_manipulation/4.jpg"
    with open("tests/images/4.jpg", "rb") as img_file:
        img_data = img_file.read()

    rsps.add(
        responses.POST,
        ims_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status=200,
    )
    rsps.add(
        responses.POST,
        image_url,
        json={
            "size": {"width": 1024, "height": 1024},
            "outputs": [
                {"seed": 123456, "image": {"url": mock_image}}
            ],
            "contentClass": "mock-art",
        },
        status=200,
    )
    # Add mock for the image download
    rsps.add(
        responses.GET,
        mock_image,
        body=img_data,
        status=200,
        content_type="image/jpeg",
    )

    return rsps


@contextlib.contextmanager
def with_maybe_use_mocks(use_mocks):
    rsps = None
    if use_mocks:
        rsps = use_requests_mock()
    try:
        yield
    finally:
        if rsps is not None:
            rsps.stop()
            rsps.reset()


def download_image(image_url: str):
    r = requests.get(image_url)
    r.raise_for_status()
    # Get the last part of the URL after the last /
    path = urlparse(image_url).path
    filename = os.path.basename(path)
    with open(filename, "wb") as f:
        f.write(r.content)
    size = len(r.content)
    typer.echo(f"Downloaded image ({size} bytes) to {filename}")


@app.command()
def generate(
    client_id: str = typer.Option(..., help="Your Adobe Firefly client ID"),
    client_secret: str = typer.Option(..., help="Your Adobe Firefly client secret"),
    prompt: str = typer.Option(..., help="Text prompt for image generation"),
    download: bool = typer.Option(False, help="Download the generated image to a file (filename is taken from the image URL)"),
    use_mocks: bool = typer.Option(False, help="Mock API responses for testing without a valid client secret."),
    format: str = typer.Option("text", help="Output format: 'text' (default) or 'json' for pretty-printed JSON response."),
    verbose: bool = typer.Option(False, help="Print status messages to stderr."),
):
    """
    Generate an image from a text prompt using Adobe Firefly API.
    """
    with with_maybe_use_mocks(use_mocks):
        _generate(client_id, client_secret, prompt, download, format, verbose)


def _generate(client_id, client_secret, prompt, download, format, verbose):
    client = FireflyClient(client_id=client_id, client_secret=client_secret)
    image_api_url = client.BASE_URL
    if verbose:
        typer.secho(f"Doing request to {image_api_url} ...", fg=typer.colors.YELLOW, err=True)
    _requests = requests
    response_obj = None
    status_code = None
    num_bytes = None
    orig_request = _requests.request

    def capture_request(*args, **kwargs):
        resp = orig_request(*args, **kwargs)
        nonlocal response_obj, status_code, num_bytes
        response_obj = resp
        status_code = resp.status_code
        try:
            num_bytes = len(resp.content)
        except Exception:
            num_bytes = None
        return resp

    _requests.request = capture_request

    try:
        response = client.generate_image(prompt=prompt)
    finally:
        _requests.request = orig_request

    if verbose:
        if response_obj is not None:
            typer.secho(
                f"Received HTTP {status_code} response ({num_bytes} bytes) from {image_api_url}.",
                fg=typer.colors.YELLOW, err=True
            )
        else:
            raw_json = json.dumps(response.json())
            typer.secho(
                f"Received HTTP 200 response ({len(raw_json.encode('utf-8'))} bytes) from {image_api_url}.",
                fg=typer.colors.YELLOW, err=True
            )

    # Output formatting
    if format == "json":
        print_json(data=response.json())
    else:
        for output in response.outputs:
            image_url = output.image.url
            typer.echo(f"Generated image URL: {image_url}")
            if download:
                download_image(image_url)


if __name__ == "__main__":
    app() 