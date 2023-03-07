import os
import hashlib
from environs import Env
from transformers import pipeline
from bs4 import BeautifulSoup
import requests
import logging
from psycopg2 import pool
from sklearn.cluster import KMeans
import ast

from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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
        # if it isn't, run the summarizer and save the result in the cache
        summary = model(text[:params['max_length']],
                        max_length=params['max_length'],
                        min_length=params['min_length'],
                        do_sample=params['do_sample'])
        if 'no_cache' not in params or not params['no_cache']:
            set_cached_result(text, summary[0]['summary_text'])
        else:
            logger.info('not caching due to request parameters')
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

def format_embedding_for_database(embedding):
    return  '[' + ','.join([str(x) for x in embedding]) + ']'

def embed_text(text, batch_id):
    hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

    embedding = embedding_model.encode(text)
    embedding = format_embedding_for_database(embedding)

    conn = pl.getconn()
    cur = conn.cursor()
    cur.execute('INSERT INTO embeddings (batch_id, hash, embedding) VALUES ' +
                '(%s, %s, %s) ON CONFLICT (batch_id, hash) ' +
                'DO UPDATE SET embedding = %s RETURNING id', (batch_id, hash, embedding, embedding)) 
    # return the id of the inserted row
    row = cur.fetchone()
    id = row[0]

    conn.commit()
    # put the connection back into the pool
    pl.putconn(conn)

    return id

def closest_embeddings(embedding_id, n):
    # find the closest N embeddings to the embedding with the given id
    conn = pl.getconn()
    cur = conn.cursor()
    cur.execute('''
SELECT id, score FROM (
  SELECT id, embedding <-> (SELECT embedding FROM embeddings WHERE id = %s ) as score
  from ( select id, embedding from embeddings where batch_id = (
    select batch_id from embeddings where id = %s
    ) ) T
  limit %s 
) E WHERE score > 0 ORDER BY score ASC;
    ''', (embedding_id, embedding_id, n))

    rows = cur.fetchall()
    # put the connection back into the pool
    pl.putconn(conn)

    return rows

def persist_clusters(cur, labels):
    # the labels are a list of tuples of the form (id, cluster)
    for row in labels:
        cur.execute('UPDATE embeddings SET cluster = %s WHERE id = %s', (str(row[1]), row[0]))

# cluster the embeddings in the given batch
def cluster(batch_id, K, job_id):
    # get a connection from the pool
    conn = pl.getconn()

    # create a cursor
    cur = conn.cursor()

    # insert the record in the jobs table
    cur.execute('INSERT INTO jobs (id, type, status) VALUES (%s, %s, %s)', (job_id, 'clustering', 'running'))

    # retrieve all the embeddings in the batch
    cur.execute('SELECT id, embedding FROM embeddings WHERE batch_id = %s', (batch_id,))
    rows = cur.fetchall()

    # extract the embeddings
    embeddings = [ast.literal_eval(row[1]) for row in rows]

    # cluster the embeddings
    clusters = KMeans(n_clusters=K, algorithm='lloyd',
                      init='k-means++', n_init=10, random_state=0).fit(embeddings)

    # combine the cluster labels with the embedding ids
    # and persist them in the database
    combined = [(row[0], clusters.labels_[i]) for i, row in enumerate(rows)]

    # persist the clusters 
    persist_clusters(cur, combined)

    # update the job status
    cur.execute('UPDATE jobs SET status = %s WHERE id = %s', ('complete', job_id))

    # commit the query
    conn.commit()

    # put the connection back into the pool
    pl.putconn(conn)

# retrieve the job status from the database by id
def get_job_status(id):
    conn = pl.getconn()
    cur = conn.cursor()
    cur.execute('SELECT status FROM jobs WHERE id = %s', (id,))
    row = cur.fetchone()
    pl.putconn(conn)
    # if the job doesn't exist, return None
    if not row:
        return None
    else:
        status = row[0]
        return status
