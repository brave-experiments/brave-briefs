# Summary

Implements a simple Python Flask RESTful server that takes in article text to summarize and produces a JSON output with a summary


# Usage

Start the server:

`python3 ./main.py`


Issue a client side curl request from a sample file:

```
# sample/https-by-default.txt
echo '{"text": "'"$(cat sample/https-by-default.txt | sed 's/"/\\\"/g' | tr -d '\r\n')"'"}' | base64 | curl -X POST -H "Content-Type: application/json" -H "Content-Encoding: base64" --data-binary @- http://localhost:5000/summarize

# sample/ethereum-2.txt
echo '{"text": "'"$(cat sample/ethereum-2.txt | sed 's/"/\\\"/g' | tr -d '\r\n')"'"}' | base64 | curl -X POST -H "Content-Type: application/json" -H "Content-Encoding: base64" --data-binary @- http://localhost:5000/summarize
```

Or directly using a JSON string:

```
curl -X POST -H "Content-Type: application/json" -d '{"text": "The extremely quick brown fox jumps over the super lazy dog."}' http://localhost:5000/summarize
```

```
curl -X POST -H "Content-Type: application/json" -d '{"url": "https://gizmodo.com/usa-weather-half-cold-half-hot-february-forecast-1850140076","max_length":330}' http://localhost:5000/page
```

As demonstrated above, data can be sent in with base64 content encoding or directly in JSON.

The following summarization parameters may be passed in the json:

  max_length [int] - maximum length of the message
  min_length [int] - minimum length of the message
  do_sample [bool]

# Environment Variables (all optional)

  DB_HOST=localhost
  DB_DBNAME=database_name
  MODEL=facebook/bart-large

# Development

Create a new virtual environment:

`python3 -m venv env`

Activate the virtual environment:

`source ./env/bin/activate`

Install the requirements:

`pip3 install -r requirements.txt`

To generate a new requirements file:

`pip freeze > requirements.txt`

To enable Postgres caching

`createdb summarizer`
`psql summarizer < migrations/0001-initial.sql`

  Create a .env file and set DB_HOST and DB_DBNAME
