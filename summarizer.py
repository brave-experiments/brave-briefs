import os
import hashlib
from environs import Env
from transformers import pipeline
import logging
from psycopg2 import pool

env = Env()
env.read_env()

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the BART model
model_name = os.environ.get("MODEL") or 'facebook/bart-large-cnn'
logger.info(f"Loading model {model_name}...")
model = pipeline('summarization', model=model_name)

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
        return result
    else:
        # if we're not using Postgres, just return None
        return None

def set_cached_result(key, result):
    hash = hashlib.sha256(key.encode('utf-8')).hexdigest()

    # save the result in the cache
    if os.environ.get("DB_HOST"):
        # get a connection from the pool
        conn = pl.getconn()
        # create a cursor
        cur = conn.cursor()
        # execute the query
        cur.execute('INSERT INTO cache (hash, result) VALUES (%s, %s) ON CONFLICT (hash) DO NOTHING', (hash, result))
        # commit the query
        conn.commit()
        # put the connection back into the pool
        pl.putconn(conn)

def summarize_text(text):
    # check if the text is in the cache
    cached_result = get_cached_result(text)
    if cached_result:
        # if it is, return the cached result
        return cached_result
    else:
        # if it isn't, run the summarizer and save the result in the cache
        summary = model(text[:3000], max_length=100, min_length=30, do_sample=False)
        set_cached_result(text, summary[0]['summary_text'])
        return summary[0]['summary_text']
