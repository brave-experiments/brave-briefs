import os
import hashlib
from environs import Env
from transformers import pipeline, BartForConditionalGeneration, BartTokenizer, PretrainedConfig
from bs4 import BeautifulSoup
import requests
import logging
from psycopg2 import pool
import torch
import os

env = Env()
env.read_env()

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the BART model
model_name = os.environ.get("MODEL") or 'facebook/bart-large-cnn'
logger.info(f"Loading model {model_name}...")
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)
if os.path.exists(model_name):
  logger.info(f"Model {model_name} loaded locally.")
else:
  logger.info(f"Model {model_name} loaded from the hub.")

# initialize Postgres connection pool
pl = None
if os.environ.get("DB_HOST"):
    logger.info(f"Using Postgres cache at {os.environ.get('DB_HOST')}")
    # initialize Postgres connection pool
    pl = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.environ.get("DB_HOST"),
        dbname=os.environ.get("DB_DBNAME"),
    )


def get_cached_result(key):
    hash = hashlib.sha256(key.encode('utf-8')).hexdigest()

    # check if the key exists in the cache
    # if it does, return the cached result
    # if it doesn't, return None
    if os.environ.get("DB_HOST"):
        # get a connection from the pool
        conn = pl.getconn()
        # create a cursor
        cur = conn.cursor()
        # execute the query
        cur.execute('SELECT result FROM cache WHERE hash = %s', (hash,))
        # get the result
        result = cur.fetchone()
        # put the connection back into the pool
        pl.putconn(conn)
        # return the result
        return result[0] if result else None
    else:
        # if we're not using Postgres, just return None
        return None


def set_cached_result(key, result):
    hash = hashlib.sha256(key.encode('utf-8')).hexdigest()

    # save the result in the cache
    if os.environ.get("DB_HOST"):
        logger.info('caching results')
        # get a connection from the pool
        conn = pl.getconn()
        # create a cursor
        cur = conn.cursor()
        # execute the query
        cur.execute('INSERT INTO cache (hash, result) VALUES ' +
                    '(%s, %s) ON CONFLICT (hash) DO NOTHING', (hash, result))
        # commit the query
        conn.commit()
        # put the connection back into the pool
        pl.putconn(conn)
    else:
        logger.info('skipping cache as database not configured')
        return None


def summarize_text(text, params):
    # check if the text is in the cache
    cached_result = get_cached_result(text)
    if cached_result:
        # if it is, return the cached result
        logger.info('returning cached result')
        return cached_result
    else:
        # Initialize the BART tokenizer

        # Encode the input text using the tokenizer
        inputs = tokenizer.encode(text, return_tensors='pt')

        # if it isn't, run the summarizer and save the result in the cache
        summary_ids = model.generate(inputs,
                        max_length=params['max_length'],
                        min_length=params['min_length'],
                        do_sample=params['do_sample'])

        # Decode the summary text from the summary_ids
        summary_text = tokenizer.decode(summary_ids[0],
                                    skip_special_tokens=True)
        return summary_text

    #if 'no_cache' not in params or not params['no_cache']:
    #        set_cached_result(text, summary[0]['summary_text'])
    #    else:
    #        logger.info('not caching due to request parameters')
        return summary[0]['summary_text']


def summarize_page(url, params):
    # use beautiful soup to get the text from the page
    # then call summarize_text on the text

    # get the text from the page
    page = requests.get(url)

    # create a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the article element's text or the full page text if not found
    article = soup.find('article')
    if article:
        text = article.get_text()
    else:
        text = soup.get_text()

    # summarize the text
    summary = summarize_text(text, params)

    return summary


def train(text, summary_text):
    # Encode the input and summary text using the tokenizer
    input_ids = tokenizer.encode(text, return_tensors='pt')
    output_ids = tokenizer.encode(summary_text, return_tensors='pt')

    # Define the model's hyperparameters and optimizer
    learning_rate = 1e-5
    num_epochs = 3
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Train the model
    model.train()
    for epoch in range(num_epochs):
        # Forward pass
        outputs = model(input_ids, labels=output_ids)

        # Compute the loss
        loss = outputs.loss

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Update the parameters
        optimizer.step()

    # Save the trained model
    model.save_pretrained(model_name)
    # After we save locally with the same model name, it'll also look for the tokenizer json
    tokenizer.save_pretrained(model_name)
