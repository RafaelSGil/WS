import csv
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from urllib.parse import quote

n = Namespace("http://ws.org/netflix_info/")
pred = Namespace("http://ws.org/netflix_info/pred/")

g = Graph()

# Helper function to generate unique URIs for values
def generate_uri(value, prefix):
    return URIRef(n + prefix + '_' + value.replace(' ', '_'))

with open('netflix_titles.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        show_uri = n['s' + row['show_id']]
        
        # Add triples for each attribute
        for column in ['type', 'title', 'director', 'country', 'date_added', 'release_year', 'rating', 'duration']:
            encoded_value = quote(row[column], safe='')
            attribute_uri = generate_uri(encoded_value, column)
            g.add((show_uri, pred[column], attribute_uri))
            g.add((attribute_uri, pred.real_name, Literal(row[column])))

        # Encode description value properly
        description_value = quote(row['description'], safe='')
        description_uri = generate_uri(description_value, 'description')
        g.add((show_uri, pred.description, description_uri))
        g.add((description_uri, pred.real_name, Literal(row['description'])))

        # For cast and listed_in columns, because in the csv 
        # they are strings of values separated by commas
        for column in ['cast', 'listed_in']:
            values = row[column].split(',')
            for value in values:
                value = value.strip()
                if value:
                    encoded_value = quote(value, safe='')
                    value_uri = generate_uri(encoded_value, column)
                    g.add((show_uri, pred[column], value_uri))
                    g.add((value_uri, pred.real_name, Literal(value)))

with open('netflix_titles.nt', 'wb') as f:
    f.write(g.serialize(format='nt').encode('utf-8'))

print("RDF/N-Triples file created: netflix_titles.nt")
