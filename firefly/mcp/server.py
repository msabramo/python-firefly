# Firefly MCP server using FastMCP

# Standard library imports
import os
from typing import Optional

# Third-party imports
from fastmcp import FastMCP

# Local imports
from firefly.client import FireflyClient

mcp = FastMCP("Adobe Firefly Image Generation MCP Server")


@mcp.tool()
def generate_image(
    prompt: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    num_variations: int = 1,
    style: Optional[dict] = None,
    structure: Optional[dict] = None,
    prompt_biasing_locale_code: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    aspect_ratio: Optional[str] = None,
    output_format: Optional[str] = None,
    content_class: Optional[str] = None,
) -> dict:
    """
    Generate an image using Adobe Firefly API.
    Args:
        prompt (str): The text prompt for image generation.
        client_id (str, optional): Firefly client ID. If not provided, uses FIREFLY_CLIENT_ID env var.
        client_secret (str, optional): Firefly client secret. If not provided, uses FIREFLY_CLIENT_SECRET env var.
        num_variations, style, structure, prompt_biasing_locale_code, negative_prompt, seed, aspect_ratio, output_format, content_class: FireflyClient.generate_image params.
    Returns:
        dict: The Firefly image response as a dict.
    """

    client_id = client_id or os.environ.get("FIREFLY_CLIENT_ID")
    client_secret = client_secret or os.environ.get("FIREFLY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "client_id and client_secret must be provided as arguments or environment variables."
        )
    style_arg = style or None
    structure_arg = structure or None
    client = FireflyClient(client_id=client_id, client_secret=client_secret)
    response = client.generate_image(
        prompt=prompt,
        num_variations=num_variations,
        style=style_arg,
        structure=structure_arg,
        prompt_biasing_locale_code=prompt_biasing_locale_code,
        negative_prompt=negative_prompt,
        seed=seed,
        aspect_ratio=aspect_ratio,
        output_format=output_format,
        content_class=content_class,
    )
    return response.json() or {
        "size": {"width": response.size.width, "height": response.size.height},
        "outputs": [
            {"seed": o.seed, "image": {"url": o.image.url}} for o in response.outputs
        ],
        "contentClass": response.contentClass,
    }


if __name__ == "__main__":
    mcp.run()
