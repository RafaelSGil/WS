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
    form = SearchForm()
    between_dates_form = BetweenDatesForm()
    date_form = DateForm()
    results = None
    all_result = None
    search_performed = False

    if request.method == 'POST':
        # Determine which form is being submitted
        if 'movie_search' in request.POST:
            form = SearchForm(request.POST)
            if form.is_valid():
                query = form.cleaned_data['search_query']
                results = unified_search(query)
                search_performed = True
        elif 'between_dates_search' in request.POST:
            between_dates_form = BetweenDatesForm(request.POST)
            if between_dates_form.is_valid():
                date1 = between_dates_form.cleaned_data['date1']
                date2 = between_dates_form.cleaned_data['date2']
                results = between_dates_search(date1, date2)
                search_performed = True
        elif 'date_search' in request.POST:
            date_form = DateForm(request.POST)
            if date_form.is_valid():
                date = date_form.cleaned_data['date']
                results = date_search(date)
                search_performed = True

        if not results:
            all_result = fetch_all_movies()

        print(results)
    context = {
        'form': form,
        'all_result': all_result,
        'between_dates_form': between_dates_form,
        'date_form': date_form,
        'results': results,
        'search_performed': search_performed,
    }
    return render(request, 'home.html', context)



def unified_search(query):
    
    genres = fetch_genres(accessor, repo_name)
    directors = fetch_directors(accessor, repo_name)
    actors = fetch_actors(accessor, repo_name)


    if query in directors:
        print("DIRECTOR")
        return search_director(query)
        
    elif query in genres:
        print("GENRE")
        return genres_search(query)
    
    elif query in actors:
        print("ACTOR")
        return cast_search(query)

    else:
        print("MOVIE")
        return movie_search(query)



def search(request):
    num_results = 0
    movie_form = MovieForm()
    cast_form = CastForm()
    between_dates_form = BetweenDatesForm()
    date_form = DateForm()
    genres_form = GenresForm()
    director_form = DirectorForm()
    movie_search_results = None
    cast_search_results = None
    between_dates_search_results = None
    date_results = None
    genres_results = None
    director_results = None

    if request.method == 'POST':
        if "movie_search" in request.POST:
            movie_form = MovieForm(request.POST)
            if movie_form.is_valid():
                movie_name = movie_form.cleaned_data['movie_name']
                movie_search_results = movie_search(movie_name)
                num_results = len(movie_search_results)
        
        if "cast_search" in request.POST:
            cast_form = CastForm(request.POST)
            if cast_form.is_valid():
                cast_name = cast_form.cleaned_data['cast_name']
                cast_search_results = cast_search(cast_name)
                num_results = len(cast_search_results)

        if "between_dates_search" in request.POST:
            between_dates_form = BetweenDatesForm(request.POST)
            if between_dates_form.is_valid():
                date1 = between_dates_form.cleaned_data['date1']
                date2 = between_dates_form.cleaned_data['date2']
                between_dates_search_results = between_dates_search(date1, date2)
                num_results = len(between_dates_search_results)

        if "date_search" in request.POST:
            date_form = DateForm(request.POST)
            if date_form.is_valid():
                date = date_form.cleaned_data['date']
                date_results = date_search(date)
                num_results = len(date_results)

        if "genres_search" in request.POST:
            genres_form = GenresForm(request.POST)
            if genres_form.is_valid():
                genres = genres_form.cleaned_data['genres']
                genres_results = genres_search(genres)
                num_results = len(genres_results)

        if "director_search" in request.POST:
            director_form = DirectorForm(request.POST)
            if director_form.is_valid():
                director = director_form.cleaned_data['director']
                director_results = search_director(director)
                num_results = len(director_results)

        return render(request, 'search.html', 
                      {'movie_form': movie_form, 
                       'cast_form': cast_form, 
                       'between_dates_form': between_dates_form,
                        'date_form': date_form,
                        'genres_form': genres_form,
                        'director_form': director_form,
                       'movie_results': movie_search_results, 
                       'cast_results': cast_search_results,
                       'between_dates_results': between_dates_search_results,
                       'date_results': date_results,
                       'genres_results': genres_results,
                       'director_results': director_results, 
                       'num_results': num_results})

    return render(request, 'search.html', {'movie_form': movie_form, 'cast_form': cast_form, 
                                           'between_dates_form': between_dates_form,
                                             'date_form': date_form, 'genres_form': genres_form,
                                             'director_form': director_form})

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

def between_dates_search(date1, date2):
    query = """
            PREFIX net: <http://ws.org/netflix_info/pred/>

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts) ?country ?date_added ?release_year ?rating ?duration (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?rel_code net:real_name ?year .
                ?show_id net:release_year ?rel_code .
                FILTER (?year >= "_date1" && ?year <= "_date2")
                
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
    query = query.replace("_date1", str(date1))
    query = query.replace("_date2", str(date2))

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)
    return res['results']['bindings']

def date_search(date):
    query = """
            PREFIX net: <http://ws.org/netflix_info/pred/>

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts) ?country ?date_added ?release_year ?rating ?duration (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?rel_code net:real_name ?year .
                ?show_id net:release_year ?rel_code .
                FILTER (?year = "_date")
                
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
    
    query = query.replace("_date", str(date))

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)

    return res['results']['bindings']

def genres_search(genres):
    genres_split = [genre.strip() for genre in genres.split(',')]

    query = """
            PREFIX net: <http://ws.org/netflix_info/pred/>

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts) 
                    ?country ?date_added ?release_year ?rating ?duration 
                    (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
            """

    for index, genre in enumerate(genres_split):
        query = query + """
                        {
                            ?genre_code net:real_name "_genre" .
                            ?show_id net:listed_in ?genre_code .
                        }
                """
        query = query.replace("_genre", genre)

        if index < len(genres_split) - 1:
            query = query + """UNION"""

    query = query + """
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

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)    
    res = json.loads(res)

    return res['results']['bindings']

def search_director(director_name):
    query = """
            PREFIX net: <http://ws.org/netflix_info/pred/>

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts) ?country ?date_added ?release_year ?rating ?duration (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?dir_code net:real_name "_director_name" .
                ?show_id net:director ?dir_code .
                
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
    
    query = query.replace("_director_name", director_name)
    
    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)    
    res = json.loads(res)

    return res['results']['bindings']







#Fetch Data from Database

def fetch_directors(accessor, repo_name):
    query = """
    PREFIX net: <http://ws.org/netflix_info/pred/>
    SELECT DISTINCT ?director WHERE {
        ?show_id net:director ?director_code .
        ?director_code net:real_name ?director .
    }
    """
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    directors = json.loads(res)
    director_list = [director['director']['value'] for director in directors['results']['bindings']]
    return director_list

def fetch_actors(accessor, repo_name):
    query = """
    PREFIX net: <http://ws.org/netflix_info/pred/>
    SELECT DISTINCT ?actor WHERE {
        ?show_id net:cast ?cast_code .
        ?cast_code net:real_name ?actor .
    }
    """
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    actors = json.loads(res)
    actor_list = [actor['actor']['value'] for actor in actors['results']['bindings']]
    return actor_list

def fetch_genres(accessor, repo_name):
    query = """
    PREFIX net: <http://ws.org/netflix_info/pred/>
    SELECT DISTINCT ?genre WHERE {
        ?show_id net:listed_in ?genre_code .
        ?genre_code net:real_name ?genre .
    }
    """
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    genres = json.loads(res)
    genre_list = [genre['genre']['value'] for genre in genres['results']['bindings']]
    return genre_list

def fetch_all_movies():
    query = """
            PREFIX netflix: <http://ws.org/netflix_info/pred/>
            SELECT ?movies ?description WHERE {
                ?fa netflix:title ?movies_code .
                ?movies_code netflix:real_name ?movies .
                ?fa netflix:description ?description_code .
                ?description_code netflix:real_name ?description .
            }
        """
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    return json.loads(res)["results"]["bindings"]