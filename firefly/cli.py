# third party imports
import typer

# local imports
from firefly import FireflyClient


app = typer.Typer()

@app.command()
def generate(
    client_id: str = typer.Option(..., help="Your Adobe Firefly client ID"),
    client_secret: str = typer.Option(..., help="Your Adobe Firefly client secret"),
    prompt: str = typer.Option(..., help="Text prompt for image generation"),
    output_file: str = typer.Option(None, help="Optional file to save the image URL"),
    download: bool = typer.Option(False, help="Download the generated image to a file (uses output_file as filename)"),
    use_mocks: bool = typer.Option(False, help="Mock API responses for testing without a valid client secret."),
    format: str = typer.Option("text", help="Output format: 'text' (default) or 'json' for pretty-printed JSON response."),
    verbose: bool = typer.Option(False, help="Print status messages to stderr."),
):
    """
    Generate an image from a text prompt using Adobe Firefly API.
    """
    if use_mocks:
        import responses
        ims_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        image_url = "https://firefly-api.adobe.io/v3/images/generate"
        mock_image = "https://example.com/fake-image.jpg"
        with responses.RequestsMock() as rsps:
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
            _generate(client_id, client_secret, prompt, output_file, download, format, verbose)
    else:
        _generate(client_id, client_secret, prompt, output_file, download, format, verbose)

def _generate(client_id, client_secret, prompt, output_file, download, format, verbose):
    client = FireflyClient(client_id=client_id, client_secret=client_secret)
    image_api_url = client.BASE_URL
    if verbose:
        typer.secho(f"Doing request to {image_api_url} ...", fg=typer.colors.YELLOW, err=True)
    import requests as _requests
    import json as _json
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
    image_url = response.outputs[0].image.url
    if verbose:
        if response_obj is not None:
            typer.secho(
                f"Received HTTP {status_code} response ({num_bytes} bytes) from {image_api_url}.",
                fg=typer.colors.YELLOW, err=True
            )
        else:
            raw_json = _json.dumps({
                "outputs": [
                    {"image": {"url": image_url}, "seed": response.outputs[0].seed}
                ],
                "size": {"width": response.size.width, "height": response.size.height},
                "contentClass": response.contentClass,
            })
            typer.secho(
                f"Received HTTP 200 response ({len(raw_json.encode('utf-8'))} bytes) from {image_api_url}.",
                fg=typer.colors.YELLOW, err=True
            )
    # Output formatting
    if format == "json":
        from rich import print_json
        def response_to_dict(resp):
            return {
                "size": {"width": resp.size.width, "height": resp.size.height},
                "outputs": [
                    {"seed": o.seed, "image": {"url": o.image.url}} for o in resp.outputs
                ],
                "contentClass": resp.contentClass,
            }
        print_json(_json.dumps(response_to_dict(response), indent=2))
    else:
        typer.echo(f"Generated image URL: {image_url}")
    if output_file:
        if download:
            import requests
            r = requests.get(image_url)
            r.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(r.content)
            typer.echo(f"Image downloaded to {output_file}")
        else:
            with open(output_file, "w") as f:
                f.write(image_url + "\n")
            typer.echo(f"Image URL saved to {output_file}")

if __name__ == "__main__":
    app() 