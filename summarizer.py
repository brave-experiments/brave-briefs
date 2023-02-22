from transformers import pipeline
from bs4 import BeautifulSoup
import requests

# Load the BART model
model = pipeline('summarization', model='facebook/bart-large-cnn')


def summarize_text(text, data):
    print('summarizing text with params: ', data)
    summary = model(text[:data['max_length']], data['max_length'],
                    data['min_length'], data['do_sample'])
    return summary[0]['summary_text']


def summarize_page(url, data):
    # use beautiful soup to get the text from the page
    # then call summarize_text on the text

    # get the text from the page
    page = requests.get(url)

    # create a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the text
    text = soup.get_text()

    # summarize the text
    summary = summarize_text(text, data)

    return summary
