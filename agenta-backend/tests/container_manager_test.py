import unittest
from unittest.mock import AsyncMock, patch
from httpx import Response

from agenta_backend.services.container_manager import get_templates_info


class TestGetTemplatesInfo(unittest.TestCase):

    @patch('my_module.httpx.AsyncClient')
    def test_get_templates_info_success(self, mock_client):
        mock_response = Response(200, json={'templates': ['template1', 'template2']})
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        url = "http://admin:admin123@127.0.0.1:5000/v2/kedeai/agent_app/tags/list"

        url = 'http://example.com/{}/{}'
        repo_user = 'user'
        repo_pass = 'pass'

        expected_result = {'templates': ['template1', 'template2']}
        result = await get_templates_info(url, repo_user, repo_pass)

        self.assertEqual(result, expected_result)
        mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
            'http://example.com/user/pass/_catalog', timeout=10
        )

    @patch('my_module.httpx.AsyncClient')
    def test_get_templates_info_failure(self, mock_client):
        mock_response = Response(500, json={'error': 'Internal Server Error'})
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        url = 'http://example.com/{}/{}'
        repo_user = 'user'
        repo_pass = 'pass'

        expected_result = {'error': 'Internal Server Error'}
        result = await get_templates_info(url, repo_user, repo_pass)

        self.assertEqual(result, expected_result)
        mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
            'http://example.com/user/pass/_catalog', timeout=10
        )


if __name__ == '__main__':
    unittest.main()