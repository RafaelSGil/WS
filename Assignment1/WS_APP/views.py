from urllib.parse import quote
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
    results = None
    search_performed = False

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search_performed = True
            query = form.cleaned_data['search_query']
            results = unified_search(query)
            
    
    if not results:
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
        res = json.loads(res)
        all_result = res["results"]["bindings"]
    else:
        all_result = None
    
    return render(request, 'home.html', {'form': form, 'results': results, 'all_result': all_result, 'search_performed': search_performed})


def delete(request):
    delete_form = DeleteForm()
    if request.method == 'POST':
        if 'delete' in request.POST:
            delete_form = DeleteForm(request.POST)
            if delete_form.is_valid():
                value = delete_form.cleaned_data['delete']

                query = """
                            PREFIX pred: <http://ws.org/netflix_info/pred/>
                            PREFIX net: <http://ws.org/netflix_info/>

                            DELETE DATA {
                                net:_encoded pred:real_name "_value" .
                            }
                        """
        
                encoded_value = value.replace(' ', '_')
                encoded_value = quote(value, safe='')

                query = query.replace("_encoded", encoded_value)
                query = query.replace("_value", value)

                payload_query = { "query": query }
                res = accessor.sparql_select(body=payload_query, repo_name=repo_name)    
                res = json.loads(res)

    return render(request, 'delete.html', {'delete_form': delete_form})


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
    prompt = None
    prompt2 = None

    if request.method == 'POST':
        if "movie_search" in request.POST:
            movie_form = MovieForm(request.POST)
            if movie_form.is_valid():
                prompt = movie_form.cleaned_data['movie_name']
                movie_search_results = movie_search(prompt)
                num_results = len(movie_search_results)
        
        if "cast_search" in request.POST:
            cast_form = CastForm(request.POST)
            if cast_form.is_valid():
                prompt = cast_form.cleaned_data['cast_name']
                cast_search_results = cast_search(prompt)
                num_results = len(cast_search_results)

        if "between_dates_search" in request.POST:
            between_dates_form = BetweenDatesForm(request.POST)
            if between_dates_form.is_valid():
                prompt = between_dates_form.cleaned_data['date1']
                prompt2 = between_dates_form.cleaned_data['date2']
                between_dates_search_results = between_dates_search(prompt, prompt2)
                num_results = len(between_dates_search_results)

        if "date_search" in request.POST:
            date_form = DateForm(request.POST)
            if date_form.is_valid():
                prompt = date_form.cleaned_data['date']
                date_results = date_search(prompt)
                num_results = len(date_results)

        if "genres_search" in request.POST:
            genres_form = GenresForm(request.POST)
            if genres_form.is_valid():
                prompt = genres_form.cleaned_data['genres']
                genres_results = genres_search(prompt)
                num_results = len(genres_results)

        if "director_search" in request.POST:
            director_form = DirectorForm(request.POST)
            if director_form.is_valid():
                prompt = director_form.cleaned_data['director']
                director_results = search_director(prompt)
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
                       'num_results': num_results,
                       'prompt': prompt,
                       'prompt2': prompt2})

    return render(request, 'search.html', {'movie_form': movie_form, 'cast_form': cast_form, 
                                           'between_dates_form': between_dates_form,
                                             'date_form': date_form, 'genres_form': genres_form,
                                             'director_form': director_form})

def search_alternative(request):
    num_results = 0
    movie_form = MovieForm()
    cast_form = CastForm()
    between_dates_form = BetweenDatesForm()
    date_form = DateForm()
    genres_form = GenresForm()
    director_form = DirectorForm()
    cast_search_results = None
    date_results = None
    genres_results = None
    director_results = None
    prompt = None

    if request.method == 'POST':
        if "cast_search" in request.POST:
            prompt = request.POST.get('cast_search')
            cast_search_results = cast_search(prompt)
            num_results = len(cast_search_results)
                
        
        if "date_search" in request.POST:
            prompt = request.POST.get('date_search')
            date_results = date_search(prompt)
            num_results = len(date_results)

        if "genre_search" in request.POST:
            prompt = request.POST.get('genre_search')
            genres_results = genres_search(prompt)
            num_results = len(genres_results)

        if "director_search" in request.POST:
            prompt = request.POST.get('director_search')
            director_results = search_director(prompt)
            num_results = len(director_results)

        return render(request, 'search.html', 
                      {'movie_form': movie_form, 
                       'cast_form': cast_form, 
                       'between_dates_form': between_dates_form,
                        'date_form': date_form,
                        'genres_form': genres_form,
                        'director_form': director_form,
                       'cast_results': cast_search_results,
                       'date_results': date_results,
                       'genres_results': genres_results,
                       'director_results': director_results, 
                       'num_results': num_results,
                       'prompt': prompt})

    return render(request, 'search.html', {'movie_form': movie_form, 'cast_form': cast_form, 
                                           'between_dates_form': between_dates_form,
                                             'date_form': date_form, 'genres_form': genres_form,
                                             'director_form': director_form})

def transform_json(json_data):
    if not json_data:
        return json_data

    for obj in json_data:
        merged_casts = obj.get('mergedCasts', {}).get('value', '')
        if not merged_casts:
            continue

        cast_list = merged_casts.split(', ')
        cast_values = {index + 1: cast for index, cast in enumerate(cast_list)}

        obj['mergedCasts'] = {'type': 'literal', 'values': cast_values}

        merged_genres = obj.get('mergedGenres', {}).get('value', '')
        if not merged_genres:
            continue

        genres_list = merged_genres.split(', ')
        genres_values = {index + 1: genre for index, genre in enumerate(genres_list)}

        obj['mergedGenres'] = {'type': 'literal', 'values': genres_values}

    return json_data


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

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js


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

    mod_js =  transform_json(res['results']['bindings'])

    print("CAST: ")
    print(mod_js)

    return mod_js


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

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js

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

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js

def genres_search(genres):
    print("GENRE: " + genres)
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

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js

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

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js


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
    
