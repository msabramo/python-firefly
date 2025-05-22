from firefly.models import FireflyImageSize, FireflyImage, FireflyImageOutput, FireflyImageResponse
from unittest.mock import Mock


def test_firefly_image_size():
    size = FireflyImageSize(width=128, height=256)
    assert size.width == 128
    assert size.height == 256


def test_firefly_image():
    img = FireflyImage(url="http://example.com/image.png")
    assert img.url == "http://example.com/image.png"


def test_firefly_image_output():
    img = FireflyImage(url="http://example.com/image.png")
    output = FireflyImageOutput(seed=42, image=img)
    assert output.seed == 42
    assert output.image == img


def test_firefly_image_response_json_with_response():
    mock_response = Mock()
    mock_response.json.return_value = {"foo": "bar"}
    size = FireflyImageSize(width=64, height=64)
    img = FireflyImage(url="http://example.com/image.png")
    output = FireflyImageOutput(seed=1, image=img)
    resp = FireflyImageResponse(size=size, outputs=[output], _response=mock_response)
    assert resp.json() == {"foo": "bar"}
    mock_response.json.assert_called_once()


def test_firefly_image_response_json_without_response():
    size = FireflyImageSize(width=64, height=64)
    img = FireflyImage(url="http://example.com/image.png")
    output = FireflyImageOutput(seed=1, image=img)
    resp = FireflyImageResponse(size=size, outputs=[output], _response=None)
    assert resp.json() is None


def test_firefly_image_response_content_class():
    size = FireflyImageSize(width=32, height=32)
    img = FireflyImage(url="http://example.com/image.png")
    output = FireflyImageOutput(seed=2, image=img)
    resp = FireflyImageResponse(size=size, outputs=[output], contentClass="test-class")
    assert resp.contentClass == "test-class"