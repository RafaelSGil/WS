from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient

from WS_APP.forms import *

# graphDB setup

endpoint = "http://localhost:7200"
repo_name = "MoviePedia"
client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    query = """
                        PREFIX netflix: <http://ws.org/netflix_info/pred/>

                        SELECT ?movies ?description
                        WHERE {
                            ?fa netflix:title ?movies_code .
                            ?movies_code netflix:real_name ?movies .
                            ?fa netflix:description ?description_code .
                            ?description_code netflix:real_name ?description .
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
                PREFIX net: <http://ws.org/netflix_info/pred/>

                SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
                        ?country ?date_added ?release_year ?rating ?duration 
                        (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
                WHERE {
                    ?title_code net:real_name "_movie_name" .
                    ?show_id net:title ?title_code .
                    
                    ?show_id net:type ?type_code .
                    ?type_code net:real_name ?type .
                    
                    ?title_code net:real_name ?title .
                    
                    ?show_id net:director ?director_code .
                    ?director_code net:real_name ?director .
                    
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    
                    ?show_id net:country ?country_code .
                    ?country_code net:real_name ?country .
                    
                    ?show_id net:date_added ?date_code .
                    ?date_code net:real_name ?date_added .
                    
                    ?show_id net:release_year ?release_code .
                    ?release_code net:real_name ?release_year .
                    
                    ?show_id net:rating ?rating_code .
                    ?rating_code net:real_name ?rating .
                    
                    ?show_id net:duration ?duration_code .
                    ?duration_code net:real_name ?duration .
                    
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    
                    ?show_id net:description ?description_code .
                    ?description_code net:real_name ?description .
                }
                GROUP BY ?type ?title ?director ?country ?date_added ?release_year ?duration ?rating ?description
                    """
    
    query = query.replace("_movie_name", movie_name)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    return res['results']['bindings']

def cast_search(cast_name):
    query = """
                PREFIX net: <http://ws.org/netflix_info/pred/>

                SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts) ?country ?date_added ?release_year ?rating ?duration (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
                WHERE {
                    ?castMember_code net:real_name "_cast_name" .
                    ?show_id net:cast ?castMember_code .
                    
                    ?show_id net:type ?type_code .
                    ?type_code net:real_name ?type .
                    
                    ?show_id net:title ?title_code .
                    ?title_code net:real_name ?title .
                    
                    ?show_id net:director ?director_code .
                    ?director_code net:real_name ?director .
                    
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    
                    ?show_id net:country ?country_code .
                    ?country_code net:real_name ?country .
                    
                    ?show_id net:date_added ?date_code .
                    ?date_code net:real_name ?date_added .
                    
                    ?show_id net:release_year ?release_code .
                    ?release_code net:real_name ?release_year .
                    
                    ?show_id net:rating ?rating_code .
                    ?rating_code net:real_name ?rating .
                    
                    ?show_id net:duration ?duration_code .
                    ?duration_code net:real_name ?duration .
                    
                    ?show_id net:listed_in ?genres_code .
                    ?genres_code net:real_name ?genres .
                    
                    ?show_id net:description ?desc_code .
                    ?desc_code net:real_name ?description .
                }
                GROUP BY ?type ?title ?director ?country ?date_added ?release_year ?rating ?duration ?description
            """
    
    query = query.replace("_cast_name", cast_name)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    return res['results']['bindings']