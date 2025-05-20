# stdlib imports
import contextlib
import json
import os
from urllib.parse import urlparse

# third party imports
import requests
import responses
from rich import print_json
import subprocess
import typer

# local imports
from firefly import FireflyClient


app = typer.Typer()

image_app = typer.Typer()


mock_image = "https://developer.adobe.com/firefly-services/docs/static/82044b6fe3cf44ec68c4872f784cd82d/96d48/cat-coding.png"


def use_requests_mock():
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()

    ims_url = "https://ims-na1.adobelogin.com/ims/token/v3"
    image_url = "https://firefly-api.adobe.io/v3/images/generate"
    mock_image_path = os.path.join(os.path.dirname(__file__), "..", "tests", "images", "cat-coding.png")
    with open(mock_image_path, "rb") as img_file:
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


@image_app.command()
def generate(
    client_id: str = typer.Option(
        None,
        help="Your Adobe Firefly client ID",
        envvar=["FIREFLY_CLIENT_ID"],
    ),
    client_secret: str = typer.Option(
        None,
        help="Your Adobe Firefly client secret",
        envvar=["FIREFLY_CLIENT_SECRET"],
    ),
    prompt: str = typer.Option(..., help="Text prompt for image generation"),
    num_variations: int = typer.Option(None, help="Number of images to generate (numVariations)"),
    style: str = typer.Option(None, help="Style object as JSON string (presets, imageReference, strength, etc.)"),
    structure: str = typer.Option(None, help="Structure object as JSON string (strength, imageReference, etc.)"),
    prompt_biasing_locale_code: str = typer.Option(None, help="Locale code for prompt biasing (promptBiasingLocaleCode)"),
    negative_prompt: str = typer.Option(None, help="Negative prompt to avoid certain content"),
    seed: int = typer.Option(None, help="Seed for deterministic output"),
    aspect_ratio: str = typer.Option(None, help="Aspect ratio, e.g. '1:1', '16:9'"),
    output_format: str = typer.Option(None, help="Output format, e.g. 'jpeg', 'png'"),
    content_class: str = typer.Option(None, help="Content class: 'photo' or 'art'"),
    download: bool = typer.Option(False, help="Download the generated image to a file (filename is taken from the image URL)"),
    show_images: bool = typer.Option(False, help="Display the image in the terminal after download."),
    use_mocks: bool = typer.Option(False, help="Mock API responses for testing without a valid client secret."),
    format: str = typer.Option("text", help="Output format: 'text' (default) or 'json' for pretty-printed JSON response."),
    verbose: bool = typer.Option(False, help="Print status messages to stderr."),
):
    """
    Generate an image from a text prompt using Adobe Firefly API.
    """
    if not client_id:
        raise typer.BadParameter("client_id must be provided as an option or via the FIREFLY_CLIENT_ID environment variable.")
    if not client_secret:
        raise typer.BadParameter("client_secret must be provided as an option or via the FIREFLY_CLIENT_SECRET environment variable.")
    if num_variations is not None and not (1 <= num_variations <= 4):
        typer.secho("--num-variations must be between 1 and 4", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=-1)
    # Parse JSON for style/structure if provided
    style_obj = None
    if style:
        try:
            style_obj = json.loads(style)
        except Exception as e:
            raise typer.BadParameter(f"Invalid JSON for --style: {e}")
    structure_obj = None
    if structure:
        try:
            structure_obj = json.loads(structure)
        except Exception as e:
            raise typer.BadParameter(f"Invalid JSON for --structure: {e}")
    try:
        with with_maybe_use_mocks(use_mocks):
            _generate(
                client_id, client_secret, prompt, download, show_images, format, verbose,
                num_variations=num_variations,
                style=style_obj,
                structure=structure_obj,
                prompt_biasing_locale_code=prompt_biasing_locale_code,
                negative_prompt=negative_prompt,
                seed=seed,
                aspect_ratio=aspect_ratio,
                output_format=output_format,
                content_class=content_class,
            )
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=-1)


def _generate(client_id, client_secret, prompt, download, show_images, format, verbose, **kwargs):
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
        num_bytes = len(resp.content)
        return resp

    _requests.request = capture_request

    try:
        response = client.generate_image(prompt=prompt, **kwargs)
    finally:
        _requests.request = orig_request

    if verbose:
        typer.secho(
            f"Received HTTP {status_code} response ({num_bytes} bytes) from {image_api_url}.",
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
            if show_images:
                try:
                    imgcat_cmd = f"imgcat --url '{image_url}'"
                    if image_url == mock_image:
                        imgcat_cmd = "imgcat tests/images/cat-coding.png"
                    subprocess.run([imgcat_cmd], shell=True, check=True)
                except Exception as e:
                    typer.secho(f"[warn] Could not display image in terminal using imgcat: {e}", fg=typer.colors.YELLOW, err=True)


app.add_typer(image_app, name="image")


if __name__ == "__main__":
    app() 