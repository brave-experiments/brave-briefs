import requests_mock
from summarizer import summarize_text, summarize_page, get_job_status
import unittest
from unittest.mock import patch


class TestSummarizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_model = patch('summarizer.model').start()
        cls.text = 'The quick brown fox jumped over the lazy dog.'
        cls.mocked_summary = 'A fox jumped.'
        cls.mock_model.side_effect = (
            lambda t, max_length, min_length, do_sample: [{
                'summary_text': cls.mocked_summary
            }] if t == cls.text else None)
        cls.data = {
                'max_length': 100,
                'min_length': 10,
                'do_sample': False,
                'no_cache': True
        }

    @classmethod
    def tearDownClass(cls):
        cls.mock_model.stop()

    def test_summarize_text(self):
        summary = summarize_text(self.text, self.data)
        self.assertEqual(summary, self.mocked_summary)

    def test_summarize_page(self):
        url = 'https://www.brianbondy.com.com'
        with requests_mock.Mocker() as m:
            m.get(url, text='<html><body><p>' +
                  self.text +
                  '</p></body></html>')
            summary = summarize_page(url, self.data)
            self.assertEqual(summary, self.mocked_summary)

    def test_summarize_page_with_article(self):
        url = 'https://www.brianbondy.com.com'
        with requests_mock.Mocker() as m:
            m.get(url, text='<html><body><div>Headers here</div><article>' +
                  self.text + '</article></body></html>')
            summary = summarize_page(url, self.data)
            self.assertEqual(summary, self.mocked_summary)



if __name__ == '__main__':
    unittest.main()
