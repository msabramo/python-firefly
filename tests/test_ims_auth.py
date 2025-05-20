import pytest
import responses
import time
from firefly.ims_auth import AdobeIMSAuth
from firefly.exceptions import FireflyAuthError

TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"

def make_auth():
    return AdobeIMSAuth(client_id="dummy_id", client_secret="dummy_secret", timeout=5)

@responses.activate
def test_get_access_token_success():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "test_token", "expires_in": 3600},
        status=200,
    )
    auth = make_auth()
    token = auth.get_access_token()
    assert token == "test_token"
    assert auth._access_token == "test_token"
    assert auth._token_expiry > time.time()

@responses.activate
def test_token_caching():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "cached_token", "expires_in": 3600},
        status=200,
    )
    auth = make_auth()
    token1 = auth.get_access_token()
    # Should use cached token on second call
    token2 = auth.get_access_token()
    assert token1 == token2
    assert responses.assert_call_count(TOKEN_URL, 1) is True

@responses.activate
def test_token_expiry():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "first_token", "expires_in": 1},
        status=200,
    )
    auth = make_auth()
    token1 = auth.get_access_token()
    # Simulate token expiry
    auth._token_expiry = time.time() - 10
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "second_token", "expires_in": 3600},
        status=200,
    )
    token2 = auth.get_access_token()
    assert token2 == "second_token"
    assert token1 != token2

@responses.activate
def test_get_access_token_failure():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"error": "invalid_client"},
        status=401,
    )
    auth = make_auth()
    with pytest.raises(FireflyAuthError):
        auth.get_access_token()

@responses.activate
def test_get_access_token_network_error():
    responses.add(
        responses.POST,
        TOKEN_URL,
        body=Exception("network error"),
    )
    auth = make_auth()
    with pytest.raises(FireflyAuthError):
        auth.get_access_token()

@responses.activate
def test_get_access_token_bad_response():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"not_access_token": True},
        status=200,
    )
    auth = make_auth()
    with pytest.raises(FireflyAuthError):
        auth.get_access_token() 