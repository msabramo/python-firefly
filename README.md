# Adobe Firefly Python Client

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

## Error Handling

- `FireflyAuthError`: Raised for authentication/token errors
- `FireflyAPIError`: Raised for general API errors or unexpected responses

## More Information

- [Adobe Firefly API Documentation]

[Adobe Firefly API Documentation]: https://developer.adobe.com/firefly-services/docs/firefly-api/guides/#generate-an-image