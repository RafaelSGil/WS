from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient

from WS_APP.forms import *

# graphDB setup

endpoint = "http://localhost:7200"
repo_name = "netflix_titles"
client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    query = """
                        PREFIX net: <http://ws.org/netflix_info/>

                        SELECT ?movies ?desc
                        WHERE {
                            ?fname net:title ?movies .
                            ?fname net:description ?desc .
                        }
                    """
            
    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    
    return render(request, 'home.html', {'all_result': res["results"]["bindings"]})

def search(request):
    movie_form = MovieForm()
    cast_form = CastForm()
    movie_search_results = None
    cast_search_results = None

    if request.method == 'POST':
        if "movie_search" in request.POST:
            movie_form = MovieForm(request.POST)
            if movie_form.is_valid():
                movie_name = movie_form.cleaned_data['movie_name']
                movie_search_results = movie_search(movie_name)
        
        if "cast_search" in request.POST:
            cast_form = CastForm(request.POST)
            if cast_form.is_valid():
                cast_name = cast_form.cleaned_data['cast_name']
                cast_search_results = cast_search(cast_name)

        return render(request, 'search.html', 
                      {'movie_form': movie_form, 
                       'cast_form': cast_form, 
                       'movie_results': movie_search_results, 
                       'cast_results': cast_search_results})

    return render(request, 'search.html', {'movie_form': movie_form, 'cast_form': cast_form})

def movie_search(movie_name):
    query = """
                        PREFIX net: <http://ws.org/netflix_info/>

                        SELECT ?title ?cast ?release ?genres ?director ?country ?rating ?duration ?description
                        WHERE {
                            ?movie net:title "_movie_name" .
                            ?movie net:title ?title .
                            ?movie net:cast ?cast .
                            ?movie net:release_year ?release .
                            ?movie net:listed_in ?genres .
                            ?movie net:director ?director .
                            ?movie net:country ?country .
                            ?movie net:rating ?rating .
                            ?movie net:duration ?duration .
                            ?movie net:description ?description .
                        }
                    """
    
    query = query.replace("_movie_name", movie_name)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    return res['results']['bindings']

def cast_search(cast_name):
    query = """
                PREFIX net: <http://ws.org/netflix_info/>

                SELECT ?title ?cast ?release ?genres ?director ?country ?rating ?duration ?description
                WHERE {
                    ?cast_movies net:cast ?cast .
                    FILTER (CONTAINS(?cast, "_cast_name")) .
                    ?cast_movies net:title ?title .
                    ?cast_movies net:cast ?cast .
                    ?cast_movies net:release_year ?release .
                    ?cast_movies net:listed_in ?genres .
                    ?cast_movies net:director ?director .
                    ?cast_movies net:country ?country .
                    ?cast_movies net:rating ?rating .
                    ?cast_movies net:duration ?duration .
                    ?cast_movies net:description ?description .
                }
            """
    
    query = query.replace("_cast_name", cast_name)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    return res['results']['bindings']