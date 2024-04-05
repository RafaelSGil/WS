# WS - Assignment 1

# Setup

## Create virtual env

In command line:

- python3 -m venv .venv
- source .venv/bin/acivate

## Install requirements

In command line:

- pip install -r requirements.txt

## GraphDB database

- Download GraphDB [here](https://www.ontotext.com/products/graphdb/download/)
- In GraphDB panel, got to "Setup -> Repositories -> Create New Repository" and create a new repository, naming it "MoviePedia".
- In GraphDB panel, got to "Import -> Upload RDF Files" and upload the file netfli_titles.nt, in the "Data" folder, and click the "import" button.

## Run server

In command line:

- python manage.py runserver
