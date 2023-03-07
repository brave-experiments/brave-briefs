import json
import base64
import unittest
from unittest.mock import patch
from main import app, install_defaults


class TestMain(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @patch('main.summarize_page')
    def test_summarize_a_page(self, mock_summarize_page):
        mock_summarize_page.return_value = 'A fox jumps.'
        url = 'https://www.example.com'
        data = {'max_length': 100,
                'min_length': 10,
                'do_sample': False,
                'url': url}
        response = self.app.post('/page', data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['summary'], 'A fox jumps.')
        mock_summarize_page.assert_called_once_with(url,
                                                    install_defaults(data))

    @patch('main.summarize_text')
    def test_summarize(self, mock_summarize_text):
        mock_summarize_text.return_value = 'A fox jumps.'
        data = {'max_length': 100, 'min_length': 10, 'do_sample': False,
                'text': 'The quick brown fox jumps over the lazy dog.'}
        response = self.app.post('/summarize', data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['summary'], 'A fox jumps.')
        mock_summarize_text.assert_called_once_with(data['text'],
                                                    install_defaults(data))

    @patch('main.summarize_text')
    def test_summarize_with_base64(self, mock_summarize_text):
        mock_summarize_text.return_value = 'A fox jumps.'
        data = {'max_length': 100, 'min_length': 10, 'do_sample': False,
                'text': 'The quick brown fox jumps over the lazy dog.'}
        encoded_data = base64.b64encode(json.dumps(data).encode('ascii'))
        response = self.app.post('/summarize', data=encoded_data,
                                 content_type='application/octet-stream',
                                 headers={'Content-Encoding': 'base64'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['summary'], 'A fox jumps.')
        mock_summarize_text.assert_called_once_with(data['text'],
                                                    install_defaults(data))

if __name__ == '__main__':
    unittest.main()
