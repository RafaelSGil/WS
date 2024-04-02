import csv
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF, XSD
from datetime import datetime

# Define the namespace for your specific domain
MOV = Namespace("http://movies.org/")

# Initialize an RDF graph
g = Graph()

# Function to format date_added to YYYY-MM-DD
def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None  # Return None if the date does not match the expected format

# Read the CSV file
with open('netflix_titles.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Create a new subject URI for each movie/show
        content_uri = MOV[str(row['show_id'])]

        # Add triples using the content URI as the subject
        g.add((content_uri, RDF.type, MOV.Movie if row['type'] == 'Movie' else MOV.TVShow))
        g.add((content_uri, FOAF.name, Literal(row['title'])))

        if row.get('director'):  # Check if director is not empty
            g.add((content_uri, MOV.director, Literal(row['director'])))

        if row.get('cast'):  # Check if cast is not empty
            for actor in row['cast'].split(', '):
                g.add((content_uri, MOV.cast, Literal(actor)))

        if row.get('country'):  # Check if country is not empty
            g.add((content_uri, MOV.country, Literal(row['country'])))

        date_added_formatted = format_date(row.get('date_added'))
        if date_added_formatted:  # Check if date_added is correctly formatted
            g.add((content_uri, MOV.dateAdded, Literal(date_added_formatted, datatype=XSD.date)))

        if row.get('release_year'):  # Check if release_year is not empty
            g.add((content_uri, MOV.releaseYear, Literal(int(row['release_year']), datatype=XSD.gYear)))

        if row.get('rating'):  # Check if rating is not empty
            g.add((content_uri, MOV.rating, Literal(row['rating'])))

        if row.get('duration'):  # Check if duration is not empty
            g.add((content_uri, MOV.duration, Literal(row['duration'])))

        if row.get('listed_in'):  # Check if listed_in is not empty
            for genre in row['listed_in'].split(', '):
                g.add((content_uri, MOV.genre, Literal(genre)))

        if row.get('description'):  # Check if description is not empty
            g.add((content_uri, MOV.description, Literal(row['description'])))

# Serialize the graph
g.serialize(destination='netflix_titles.nt', format='nt')

print("RDF file has been created in N-Triples format.")
