import csv
from rdflib import Graph, Literal, Namespace, RDF, URIRef

n = Namespace("http://ws.org/netflix_info/")

g = Graph()
with open('netflix_titles.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        show_uri = n[row['show_id']]
        
        g.add((show_uri, n.type, Literal(row['type'])))
        g.add((show_uri, n.title, Literal(row['title']))) 
        g.add((show_uri, n.director, Literal(row['director'])))
        g.add((show_uri, n.cast, Literal(row['cast'])))
        g.add((show_uri, n.country, Literal(row['country']))) 
        g.add((show_uri, n.date_added, Literal(row['date_added']))) 
        g.add((show_uri, n.release_year, Literal(row['release_year']))) 
        g.add((show_uri, n.rating, Literal(row['rating'])))
        g.add((show_uri, n.duration, Literal(row['duration'])))
        g.add((show_uri, n.listed_in, Literal(row['listed_in'])))
        g.add((show_uri, n.description, Literal(row['description'])))

with open('netflix_titles.nt', 'wb') as f:
    f.write(g.serialize(format='nt').encode('utf-8'))

print("RDF/N-Triples file created: netflix_titles.nt")
