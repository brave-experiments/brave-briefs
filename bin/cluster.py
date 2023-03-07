import os
import psycopg2
import argparse
from dotenv import load_dotenv
import sys

sys.path.append('..')
import summarizer

# Accept batch_id parameter from command line argument
parser = argparse.ArgumentParser()
parser.add_argument("batch_id", help="ID of the batch to cluster")
parser.add_argument("k", help="Number of clusters")
args = parser.parse_args()
batch_id = args.batch_id

# convert k to an integer
k = int(args.k)

# Call cluster method of summarizer module
summarizer.cluster(batch_id, k)
