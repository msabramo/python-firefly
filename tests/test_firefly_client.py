"""
Tests based on Firefly docs at
https://developer.adobe.com/firefly-services/docs/firefly-api/guides/#generate-an-image
"""

import pytest
import responses
import json
from firefly import (
    FireflyClient,
    FireflyAPIError,
    FireflyAuthError,
)
from unittest import mock

TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
IMAGE_URL = "https://firefly-api.adobe.io/v3/images/generate"


@pytest.fixture
def client():
    return FireflyClient(client_id="dummy_id", client_secret="dummy_secret")


@pytest.fixture
def mock_valid_ims_access_token_response():
    """
    Mock a successful response from the IMS token endpoint.

    This is used to test the client's ability to handle a valid IMS access token.

    Returns:
        None
    """
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "test_token", "expires_in": 3600},
        status=200,
    )


@responses.activate
def test_generate_image_success(client, mock_valid_ims_access_token_response):
    # Mock image generation endpoint with structure matching the Firefly docs:
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={
            "size": {
                "width": 2048,
                "height": 2048,
            },
            "outputs": [
                {
                    "seed": 1779323515,
                    "image": {
                        "url": "https://pre-signed-firefly-prod.s3-accelerate.amazonaws.com/images/asdf-12345?lots=of&query=params..."
                    },
                }
            ],
            "contentClass": "art",
        },
        status=200,
    )

    response = client.generate_image(prompt="a cat coding")
    assert response.size.width == 2048
    assert response.size.height == 2048
    assert response.contentClass == "art"
    assert len(response.outputs) == 1
    output = response.outputs[0]
    assert output.seed == 1779323515
    assert (
        output.image.url
        == "https://pre-signed-firefly-prod.s3-accelerate.amazonaws.com/images/asdf-12345?lots=of&query=params..."
    )

    # Check that both requests were made
    responses.assert_call_count(TOKEN_URL, 1)
    responses.assert_call_count(IMAGE_URL, 1)

    # Check the payload of the image generation request
    image_call = responses.calls[1]
    assert image_call.request.method == "POST"
    assert image_call.request.url == IMAGE_URL
    body = json.loads(image_call.request.body.decode())
    assert body["prompt"] == "a cat coding"
    assert image_call.request.headers["Authorization"] == "Bearer test_token"
    assert image_call.request.headers["x-api-key"] == "dummy_id"

    # Check the extra fields in the response (top-level)
    resp_json = responses.calls[1].response.json()
    assert resp_json["size"] == {"width": 2048, "height": 2048}
    assert resp_json["contentClass"] == "art"
    assert resp_json["outputs"][0]["seed"] == 1779323515
    assert (
        resp_json["outputs"][0]["image"]["url"]
        == "https://pre-signed-firefly-prod.s3-accelerate.amazonaws.com/images/asdf-12345?lots=of&query=params..."
    )


@responses.activate
def test_auth_failure(client):
    # Mock token endpoint with 401
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"error": "invalid_client"},
        status=401,
    )
    with pytest.raises(FireflyAuthError):
        client.generate_image(prompt="fail auth")


@responses.activate
def test_api_error(client, mock_valid_ims_access_token_response):
    # Mock image generation endpoint with 500
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={"error": "server error"},
        status=500,
    )
    with pytest.raises(FireflyAPIError):
        client.generate_image(prompt="fail api")


@responses.activate
def test_unexpected_response_format(client, mock_valid_ims_access_token_response):
    # Mock image generation endpoint with unexpected format
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={"unexpected": "format"},
        status=200,
    )
    with pytest.raises(FireflyAPIError):
        client.generate_image(prompt="bad response")


@responses.activate
def test_image_generation_unauthorized(client, mock_valid_ims_access_token_response):
    # Mock image generation endpoint with 401 Unauthorized
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={"error": "unauthorized"},
        status=401,
    )
    with pytest.raises(FireflyAuthError):
        client.generate_image(prompt="unauthorized access")


@responses.activate
def test_generate_image_value_error(client, mock_valid_ims_access_token_response):
    # Patch requests.request to raise ValueError
    with mock.patch("requests.request", side_effect=ValueError("bad value")):
        with pytest.raises(FireflyAPIError):
            client.generate_image(prompt="trigger value error")


@responses.activate
def test_generate_image_with_all_new_parameters(client, mock_valid_ims_access_token_response):
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={
            "size": {"width": 1024, "height": 768},
            "outputs": [
                {"seed": 123, "image": {"url": "https://example.com/image.png"}}
            ],
            "contentClass": "photo",
        },
        status=200,
    )
    style = {"presets": ["bw"], "strength": 50}
    structure = {"strength": 80, "imageReference": {"source": {"uploadId": "abc123"}}}
    response = client.generate_image(
        prompt="test prompt",
        num_variations=2,
        style=style,
        structure=structure,
        prompt_biasing_locale_code="en-US",
        negative_prompt="no text",
        seed=42,
        aspect_ratio="16:9",
        output_format="jpeg",
        extra_param="extra_value"
    )
    # Check the outgoing request body
    image_call = responses.calls[1]
    body = json.loads(image_call.request.body.decode())
    assert body["prompt"] == "test prompt"
    assert body["numVariations"] == 2
    assert body["style"] == style
    assert body["structure"] == structure
    assert body["promptBiasingLocaleCode"] == "en-US"
    assert body["negativePrompt"] == "no text"
    assert body["seed"] == 42
    assert body["aspectRatio"] == "16:9"
    assert body["outputFormat"] == "jpeg"
    assert body["extra_param"] == "extra_value"
    # Check the response is parsed correctly
    assert response.size.width == 1024
    assert response.size.height == 768
    assert response.contentClass == "photo"
    assert len(response.outputs) == 1
    assert response.outputs[0].seed == 123
    assert response.outputs[0].image.url == "https://example.com/image.png"


@responses.activate
def test_generate_image_content_class(client, mock_valid_ims_access_token_response):
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={
            "size": {"width": 512, "height": 512},
            "outputs": [
                {"seed": 1, "image": {"url": "https://example.com/img.png"}}
            ],
            "contentClass": "photo",
        },
        status=200,
    )
    # Valid value: 'photo'
    response = client.generate_image(prompt="test", content_class="photo")
    image_call = responses.calls[1]
    body = json.loads(image_call.request.body.decode())
    assert body["contentClass"] == "photo"
    assert response.contentClass == "photo"
    # Valid value: 'art'
    responses.reset()
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={
            "size": {"width": 512, "height": 512},
            "outputs": [
                {"seed": 2, "image": {"url": "https://example.com/img2.png"}}
            ],
            "contentClass": "art",
        },
        status=200,
    )
    response = client.generate_image(prompt="test", content_class="art")
    image_call = responses.calls[0]
    body = json.loads(image_call.request.body.decode())
    assert body["contentClass"] == "art"
    assert response.contentClass == "art"
    # Invalid value
    with pytest.raises(ValueError):
        client.generate_image(prompt="test", content_class="invalid")
