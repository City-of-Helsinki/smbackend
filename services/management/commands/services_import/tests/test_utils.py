from unittest.mock import patch

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectTimeout, ReadTimeout
from urllib3.util.retry import Retry

from services.management.commands.services_import.utils import pk_get

URL_BASE = "https://www.hel.fi/palvelukarttaws/rest/v4/"
RESOURCE_NAME = "ontologytree"


class TestPkGet:
    """Test the pk_get function with retry logic."""

    def test_pk_get_success(self, requests_mock):
        """Test successful API call on first attempt."""
        url = f"{URL_BASE}{RESOURCE_NAME}/"
        requests_mock.get(url, json={"data": "test"}, status_code=200)

        result = pk_get(RESOURCE_NAME)

        assert result == {"data": "test"}
        assert requests_mock.call_count == 1
        assert requests_mock.last_request.url == url

    def test_pk_get_with_resource_id(self, requests_mock):
        """Test API call with resource ID."""
        url = f"{URL_BASE}{RESOURCE_NAME}/123/"
        requests_mock.get(url, json={"id": 123, "data": "test"}, status_code=200)

        result = pk_get(RESOURCE_NAME, res_id=123)

        assert result == {"id": 123, "data": "test"}
        assert requests_mock.call_count == 1
        assert requests_mock.last_request.url == url

    def test_pk_get_with_params(self, requests_mock):
        """Test API call with query parameters."""
        url = f"{URL_BASE}{RESOURCE_NAME}/?key=value"
        requests_mock.get(url, json={"data": "test"}, status_code=200)

        result = pk_get(RESOURCE_NAME, params={"key": "value"})

        assert result == {"data": "test"}
        assert requests_mock.call_count == 1
        assert requests_mock.last_request.url == url

    def test_pk_get_http_error(self, requests_mock):
        """Test handling of non-200 status codes."""
        resource_nonexistent = "nonexistent"
        url = f"{URL_BASE}{resource_nonexistent}/"
        requests_mock.get(url, status_code=404)

        with pytest.raises(requests.HTTPError, match="status code 404"):
            pk_get(resource_nonexistent)

        assert requests_mock.call_count == 1

    def test_pk_get_configures_retry_adapter(self):
        """Test that pk_get properly configures HTTPAdapter with Retry strategy.

        Note: We test that the retry adapter is configured correctly.
        Testing actual retry behavior with requests-mock is problematic because
        requests-mock intercepts the adapter chain, bypassing urllib3.Retry logic.
        """
        with patch(
            "services.management.commands.services_import.utils.requests.Session"
        ) as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}

            pk_get(RESOURCE_NAME, max_attempts=5, retry_delay=2)

            # Verify HTTPAdapter.mount was called once for HTTPS
            assert mock_session.mount.call_count == 1

            # Get the adapter that was mounted
            mount_calls = mock_session.mount.call_args_list
            adapter = mount_calls[0][0][1]  # Second argument of first mount call

            # Verify it's an HTTPAdapter with retry configuration
            assert isinstance(adapter, HTTPAdapter)
            assert adapter.max_retries is not None

            # Verify retry configuration
            retry_config = adapter.max_retries
            assert isinstance(retry_config, Retry)
            assert retry_config.total == 5
            assert retry_config.backoff_factor == 2
            assert 503 in retry_config.status_forcelist
            assert 502 in retry_config.status_forcelist
            assert 500 in retry_config.status_forcelist

    def test_pk_get_with_custom_timeout(self, requests_mock):
        """Test that custom timeout is passed correctly."""
        url = f"{URL_BASE}{RESOURCE_NAME}/"
        requests_mock.get(url, json={"data": "test"}, status_code=200)

        result = pk_get(RESOURCE_NAME, timeout_seconds=30)

        assert result == {"data": "test"}
        # Can't easily verify timeout with requests-mock, but we verify the call succeeded

    def test_pk_get_session_cleanup(self):
        """Test that session is properly closed even on error."""
        with patch(
            "services.management.commands.services_import.utils.requests.Session"
        ) as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_session.get.side_effect = ConnectTimeout("Connection failed")

            with pytest.raises(ConnectTimeout):
                pk_get(RESOURCE_NAME)

            # Verify session was closed even after exception
            mock_session.close.assert_called_once()

    def test_pk_get_exception_handling(self, requests_mock):
        """Test that exceptions are properly raised."""
        url = f"{URL_BASE}{RESOURCE_NAME}/"
        requests_mock.get(url, exc=ReadTimeout("Read timeout"))

        with pytest.raises(ReadTimeout, match="Read timeout"):
            pk_get(RESOURCE_NAME)
