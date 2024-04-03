from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient

endpoint = "http://localhost:7200"
repo_name = "netflix_titles"
client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)

from WS_APP.forms import MovieForm

# Create your views here.
def home(request):
    """Renders the home page."""
    """assert isinstance(request, HttpRequest)"""
    
    return render(request, 'home.html')

def movie_search(request):
    if request.method == 'POST':
        if "all-movies" in request.POST:
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

            form = MovieForm()
            return render(request, 'search.html', {'form': form, 'all_result': res["results"]["bindings"]})

        form = MovieForm(request.POST)
        if form.is_valid():
            movie_name = form.cleaned_data['movie_name']
            
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

            return render(request, 'search.html', {'form': form, 'search_result': res["results"]["bindings"]})
    

    form = MovieForm()
    return render(request, 'search.html', {'form': form})