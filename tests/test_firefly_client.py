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

TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
IMAGE_URL = "https://firefly-api.adobe.io/v3/images/generate"


@pytest.fixture
def client():
    return FireflyClient(client_id="dummy_id", client_secret="dummy_secret")


@responses.activate
def test_generate_image_success(client):
    # Mock token endpoint
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "test_token", "expires_in": 3600},
        status=200,
    )
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
    assert response.size == {"width": 2048, "height": 2048}
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
def test_api_error(client):
    # Mock token endpoint
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "test_token", "expires_in": 3600},
        status=200,
    )
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
def test_unexpected_response_format(client):
    # Mock token endpoint
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "test_token", "expires_in": 3600},
        status=200,
    )
    # Mock image generation endpoint with unexpected format
    responses.add(
        responses.POST,
        IMAGE_URL,
        json={"unexpected": "format"},
        status=200,
    )
    with pytest.raises(FireflyAPIError):
        client.generate_image(prompt="bad response")
