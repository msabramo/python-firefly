# Adobe Firefly Python Client Library & CLI

[![CI](https://github.com/msabramo/python-firefly/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/msabramo/python-firefly/actions/workflows/ci.yml)

A Python client for the Adobe Firefly API,
created using the [Adobe Firefly API Documentation].

## Features

- Authenticate with Adobe Firefly using client ID and secret
- Automatically handles access token retrieval and refresh
- Generate images from text prompts
- Simple, extensible interface

## Requirements

- Python 3.10+
- `requests` library

## Quickstart

```python
from firefly import FireflyClient

client = FireflyClient(
    client_id="your-firefly-client-id",
    client_secret="your-firefly-client-secret"
)

response = client.generate_image(prompt="a realistic illustration of a cat coding")
print("Generated image URL:", response.outputs[0].image.url)
print("Seed:", response.outputs[0].seed)
print("Size:", response.size)
print("Content class:", response.contentClass)
```

## API Reference

- `FireflyClient(client_id, client_secret, timeout=30)`
  - Main entry point. Handles authentication and requests.

- `generate_image(prompt: str, **kwargs) -> FireflyImageResponse`
  - Generate an image from a text prompt. Returns a response object with attributes matching the API response (including outputs, size, contentClass, etc).
  - Additional keyword arguments are passed as parameters to the API.

## Command Line Interface (CLI)

The `firefly` CLI allows you to generate images from the command line using the Adobe Firefly API.

### Usage

```sh
export FIREFLY_CLIENT_ID="abc123"
export FIREFLY_CLIENT_SECRET="xyz456"
```

```sh
firefly image generate \
  --prompt="a realistic illustration of a cat coding" \
  --show-images
```

### Options

- `--client-id TEXT`                        Your Adobe Firefly client ID [env var: FIREFLY_CLIENT_ID] [default: None]
- `--client-secret TEXT`                    Your Adobe Firefly client secret [env var: FIREFLY_CLIENT_SECRET] [default: None]
- `--prompt TEXT` *                         Text prompt for image generation [required]
- `--num-variations INTEGER`                Number of images to generate (numVariations) [default: None]
- `--style TEXT`                            Style object as JSON string (presets, imageReference, strength, etc.) [default: None]
- `--structure TEXT`                        Structure object as JSON string (strength, imageReference, etc.) [default: None]
- `--prompt-biasing-locale-code TEXT`       Locale code for prompt biasing (promptBiasingLocaleCode), e.g., en-US, en-IN, zh-CN [default: None]
- `--negative-prompt TEXT`                  Negative prompt to avoid certain content [default: None]
- `--seed INTEGER`                          Seed for deterministic output [default: None]
- `--aspect-ratio TEXT`                     Aspect ratio, e.g. '1:1', '16:9' [default: None]
- `--output-format TEXT`                    Output format, e.g. 'jpeg', 'png' [default: None]
- `--content-class TEXT`                    Content class: 'photo' or 'art' [default: None]
- `--download/--no-download`                Download the generated image to a file (filename is taken from the image URL) [default: no-download]
- `--show-images/--no-show-images`          Display the image in the terminal after download. [default: no-show-images]
- `--use-mocks/--no-use-mocks`              Mock API responses for testing without a valid client secret. [default: no-use-mocks]
- `--format TEXT`                           Output format: 'text' (default) or 'json' for pretty-printed JSON response. [default: text]
- `--verbose/--no-verbose`                  Print status messages to stderr. [default: no-verbose]
- `--help`                                  Show this message and exit

### Example

```sh
firefly image generate \
  --prompt="a futuristic city skyline at sunset" \
  --show-images
```

The CLI will print the generated image URL.

## Error Handling

- `FireflyAuthError`: Raised for authentication/token errors
- `FireflyAPIError`: Raised for general API errors or unexpected responses

## More Information

- [Adobe Firefly API Documentation]

[Adobe Firefly API Documentation]: https://developer.adobe.com/firefly-services/docs/firefly-api/guides/#generate-an-image
