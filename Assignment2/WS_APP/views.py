from urllib.parse import quote
from django.shortcuts import render

from django.http import HttpRequest, HttpResponse, JsonResponse

import logging
import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
import requests
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
    actor_info = None

    if request.method == 'POST':
        # Determine which form is being submitted
        if 'movie_search' in request.POST:
            form = SearchForm(request.POST)
            if form.is_valid():
                query = form.cleaned_data['search_query']
                actor_info = actors_info(query)
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

    genres_grid_res = genres_grid()

    context = {
        'form': form,
        'all_result': all_result,
        'between_dates_form': between_dates_form,
        'date_form': date_form,
        'results': results,
        'search_performed': search_performed,
        'genre_grid': genres_grid_res,
        'cast_grid': ["Will Smith", "Margot Robbie", "Nicole Kidman", "Brad Pitt"],
        'director_grid': ["Steven Spielberg", "Martin Scorsese", "Quentin Tarantino", "Tim Burton"],
        'actor_info' : actor_info,
    }
    return render(request, 'home.html', context)

def genres_grid():
    query_top_genres = """
                            PREFIX net: <http://ws.org/netflix_info/pred/>

                            SELECT ?genres (COUNT(?genres) as ?count)
                            WHERE {
                                ?movie net:listed_in ?genres_code .
                                ?genres_code net:real_name ?genres .
                            }
                            GROUP BY ?genres
                            ORDER BY DESC(?count)
                            LIMIT 4
                        """
    
    payload_query = { "query": query_top_genres }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)  
    return json.loads(res)['results']['bindings']

def sparql_update(query, repo_name):
    endpoint = "http://localhost:7200/repositories/" + repo_name + "/statements"
    headers = {'Content-Type': 'application/sparql-update'}
    response = requests.post(endpoint, data=query, headers=headers)
    return response

def insert(request):
    context = {
        'success': False,
        'message': "No action performed."
    }

    if request.method == 'POST':
        # Extracting form data
        name = request.POST.get('movie_name')
        director = request.POST.get('movie_director')
        country = request.POST.get('movie_country')
        rating = request.POST.get('movie_rating')
        duration = request.POST.get('movie_duration')
        genres = request.POST.get('movie_genres').split(',')
        cast = request.POST.get('movie_cast').split(',')
        date_added = request.POST.get('movie_date_added')
        release_year = request.POST.get('movie_release_year')
        description = request.POST.get('movie_description')
        movie_type = 'Movie'  # Assuming all entries are movies for simplification

        # Generate unique IDs for the new movie using the movie name
        movie_id = name.replace(' ', '_')

        # Start the INSERT DATA block
        query = f"""
        PREFIX pred: <http://ws.org/netflix_info/pred/>
        PREFIX net: <http://ws.org/netflix_info/>
        INSERT DATA {{
            net:{movie_id} pred:show_id "{movie_id}".
            net:{movie_id} pred:type net:{movie_type}.
            net:{movie_type} pred:real_name "{movie_type}".
            net:{movie_id} pred:title net:{name.replace(' ', '_')}.
            net:{name.replace(' ', '_')} pred:real_name "{name}".
            net:{movie_id} pred:director net:{director.replace(' ', '_')}.
            net:{director.replace(' ', '_')} pred:real_name "{director}".
        """

        # Adding cast members
        for actor in cast:
            actor_id = actor.strip().replace(' ', '_')
            query += f"net:{movie_id} pred:cast net:{actor_id}.\n"
            query += f"net:{actor_id} pred:real_name \"{actor.strip()}\".\n"

        # Adding additional properties
        query += f"""
            net:{movie_id} pred:country net:Country_{country.replace(' ', '_')}.
            net:Country_{country.replace(' ', '_')} pred:real_name "{country}".
            net:{movie_id} pred:date_added net:Date_{date_added.replace('-', '_')}.
            net:Date_{date_added.replace('-', '_')} pred:real_name "{date_added}".
            net:{movie_id} pred:release_year net:Year_{release_year}.
            net:Year_{release_year} pred:real_name "{release_year}".
            net:{movie_id} pred:rating net:Rating_{rating.replace(' ', '_')}.
            net:Rating_{rating.replace(' ', '_')} pred:real_name "{rating}".
            net:{movie_id} pred:duration net:Duration_{duration.replace(' ', '_')}.
            net:Duration_{duration.replace(' ', '_')} pred:real_name "{duration}".
        """

        # Adding genres
        for genre in genres:
            genre_id = genre.strip().replace(' ', '_')
            query += f"net:{movie_id} pred:listed_in net:Genre_{genre_id}.\n"
            query += f"net:Genre_{genre_id} pred:real_name \"{genre.strip()}\".\n"

        query += f"net:{movie_id} pred:description net:Desc_{movie_id}.\n"
        query += f"net:Desc_{movie_id} pred:real_name \"{description}\".\n"
        query += "}\n"
        
      
        try:
            response = sparql_update(query, repo_name)
            if response.status_code != 200:
                context['success'] = True
                context['message'] = "Movie added successfully!"
            else:
                context['message'] = "Failed to add movie. Response: " + response.text

            return render(request, 'insert.html', context)
        except Exception as e:
            context['message'] = f"Error adding movie: {str(e)}"

    return render(request, 'insert.html', context)


def delete(request):
    success = None
    if request.method == 'POST':
        if "delete_data" in request.POST:
            value = request.POST.get("delete_value")

            query = """
                            PREFIX pred: <http://ws.org/netflix_info/pred/>
                            PREFIX net: <http://ws.org/netflix_info/>

                            DELETE DATA {
                                net:_encoded pred:real_name "_value" .
                            }
                        """
        
            encoded_value = value.replace(' ', '_')
            encoded_value = quote(encoded_value, safe='')

            query = query.replace("_encoded", encoded_value)
            query = query.replace("_value", value)
            payload_query = { "update": query }
            res = accessor.sparql_update(body=payload_query, repo_name=repo_name)  
            
            query = """
                            PREFIX pred: <http://ws.org/netflix_info/pred/>
                            PREFIX net: <http://ws.org/netflix_info/>

                            ASK {
                                net:_encoded pred:real_name "_value" .
                            }
                        """
            
            query = query.replace("_encoded", encoded_value)
            query = query.replace("_value", value)

            payload_query = { "query": query }
            success = accessor.sparql_select(body=payload_query, repo_name=repo_name)  
            success = json.loads(success)
            return render(request, 'delete.html', {'success': success})
        
        if "delete_entire_genre" in request.POST:
            value = request.POST.get("delete_value")

            query = """
                        PREFIX net: <http://ws.org/netflix_info/pred/>

                        DELETE {
                        ?show_id ?p ?o .
                        }
                        WHERE {
                        ?genres_code net:real_name "_value" .
                        ?show_id net:listed_in ?genres_code .
                        
                        ?show_id ?p ?o .
                        }
                    """
            
            query = query.replace("_value", value)
            payload_query = { "update": query }
            accessor.sparql_update(body=payload_query, repo_name=repo_name)  
            
            query = """
                        PREFIX net: <http://ws.org/netflix_info/pred/>

                        ASK
                        WHERE {
                        {
                            SELECT (COUNT(?genres) AS ?count)
                            WHERE {
                            ?movie net:listed_in ?genres_code .
                            ?genres_code net:real_name ?genres .
                            FILTER (?genres = "_value")
                            }
                            GROUP BY ?genres
                        }
                        FILTER (?count > 0)
                        }
                    """    
            
            query = query.replace("_value", value)

            payload_query = { "query": query }
            success = accessor.sparql_select(body=payload_query, repo_name=repo_name)  
            success = json.loads(success)
            return render(request, 'delete.html', {'success2': success})

    return render(request, 'delete.html')


def actors_info(actor_name):
    formatted_name = actor_name.replace(" ", "_")
    actor_uri = f"http://dbpedia.org/resource/{formatted_name}"
    
    query = f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?abstract ?birthDate ?birthPlace ?thumbnail (GROUP_CONCAT(?occupation; separator=", ") AS ?occupations) WHERE {{
      <{actor_uri}> dbo:abstract ?abstract .
      OPTIONAL {{ <{actor_uri}> dbp:birthDate ?birthDate . }}
      OPTIONAL {{ <{actor_uri}> dbp:birthPlace ?birthPlace . }}
      OPTIONAL {{ <{actor_uri}> dbo:thumbnail ?thumbnail . }}
      OPTIONAL {{ <{actor_uri}> dbp:occupation ?occupation . }}
      FILTER (lang(?abstract) = 'en')

    }}
    LIMIT 1
    """
    
    sparql_url = 'http://dbpedia.org/sparql'
    headers = {'Accept': 'application/json'}
    response = requests.get(sparql_url, params={'query': query}, headers=headers)
    #print(response.json().get('results', {}).get('bindings', []))
    print(response)
    if response.status_code == 200:
        results = response.json().get('results', {}).get('bindings', [])
        if results:
            result = results[0]
            return {
                'actor_name': actor_name,
                'abstract': result.get('abstract', {}).get('value', 'N/A'),
                'birthDate': result.get('birthDate', {}).get('value', 'N/A'),
                'birthPlace': result.get('birthPlace', {}).get('value', 'N/A'),
                'thumbnail': result.get('thumbnail', {}).get('value', 'N/A'),
                'occupations' : result.get('occupations', {}).get('value', 'N/A') 
            }
    return {
        'abstract': 'N/A',
        'birthDate': 'N/A',
        'birthPlace': 'N/A',
        'thumbnail': 'N/A',
        'occupations' : 'N/A'
    }

def get_actor_uri(actor_name):
    lookup_url = "https://lookup.dbpedia.org/api/search"
    params = {
        'query': actor_name,
        'format': 'json'
    }
    response = requests.get(lookup_url, params=params, headers={'Accept': 'application/json'})
    results = response.json()['docs']
    for result in results:
        if 'Actor' in result['rdf:type']:
            return result['resource'][0]
    return None

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
    unified_results = None
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

        if "unified_search" in request.POST:
            prompt = request.POST.get('unified_search')
            unified_results = unified_search(prompt)
            num_results = len(unified_results)

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
                       'unified_results': unified_results, 
                       'num_results': num_results,
                       'prompt': prompt})

    return render(request, 'search.html', {'movie_form': movie_form, 'cast_form': cast_form, 
                                           'between_dates_form': between_dates_form,
                                             'date_form': date_form, 'genres_form': genres_form,
                                             'director_form': director_form})


  

def unified_search(query):
    results = []

    genres = fetch_genres(accessor, repo_name)
    directors = fetch_directors(accessor, repo_name)
    actors = fetch_actors(accessor, repo_name)
    
    if query in actors:
        results.extend(cast_search(query))
        
    if query in genres:
        results.extend(genres_search(query))
    
    if query in directors:
        results.extend(search_director(query))

    if not results:
        results.extend(movie_search(query))

    return results


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

                    ?title_code net:real_name ?title .
                    
                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
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

                SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
                         ?country ?date_added ?release_year ?rating ?duration 
                         (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
                WHERE {
                    ?castMember_code net:real_name "_cast_name" .
                    ?show_id net:cast ?castMember_code .

                    OPTIONAL {
                        ?show_id net:title ?title_code .
                        ?title_code net:real_name ?title .
                    }

                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
                }
                GROUP BY ?type ?title ?director ?country ?date_added ?release_year ?rating ?duration ?description
            """
    
    query = query.replace("_cast_name", cast_name)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    res = json.loads(res)

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js


def between_dates_search(date1, date2):
    query = """
            PREFIX net: <http://ws.org/netflix_info/pred/>

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
              ?country ?date_added ?release_year ?rating ?duration 
              (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?rel_code net:real_name ?year .
                ?show_id net:release_year ?rel_code .
                FILTER (?year >= "_date1" && ?year <= "_date2")
                
                    OPTIONAL {
                        ?show_id net:title ?title_code .
                        ?title_code net:real_name ?title .
                    }

                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
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

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
              ?country ?date_added ?release_year ?rating ?duration 
              (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?rel_code net:real_name ?year .
                ?show_id net:release_year ?rel_code .
                FILTER (?year = "_date")
                
                OPTIONAL {
                        ?show_id net:title ?title_code .
                        ?title_code net:real_name ?title .
                    }

                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
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
                    OPTIONAL {
                        ?show_id net:title ?title_code .
                        ?title_code net:real_name ?title .
                    }

                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
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

            SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
              ?country ?date_added ?release_year ?rating ?duration 
              (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
            WHERE {
                ?dir_code net:real_name "_director_name" .
                ?show_id net:director ?dir_code .
                
                OPTIONAL {
                        ?show_id net:title ?title_code .
                        ?title_code net:real_name ?title .
                    }

                    OPTIONAL{
                        ?show_id net:type ?type_code .
                        ?type_code net:real_name ?type .
                    }
                    
                    OPTIONAL {
                        ?show_id net:director ?director_code .
                        ?director_code net:real_name ?director .
                    }
                    OPTIONAL {
                        ?show_id net:cast ?cast_code .
                        ?cast_code net:real_name ?cast .
                    }
                    OPTIONAL {
                        ?show_id net:country ?country_code .
                        ?country_code net:real_name ?country .
                    }
                    OPTIONAL {
                        ?show_id net:date_added ?date_code .
                        ?date_code net:real_name ?date_added .
                    }
                    OPTIONAL {
                        ?show_id net:release_year ?release_code .
                        ?release_code net:real_name ?release_year .
                    }
                    OPTIONAL {
                        ?show_id net:rating ?rating_code .
                        ?rating_code net:real_name ?rating .
                    }
                    OPTIONAL {
                        ?show_id net:duration ?duration_code .
                        ?duration_code net:real_name ?duration .
                    }
                    OPTIONAL {
                        ?show_id net:listed_in ?genres_code .
                        ?genres_code net:real_name ?genres .
                    }
                    OPTIONAL {
                        ?show_id net:description ?description_code .
                        ?description_code net:real_name ?description .
                    }
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

def fetch_all_movies():
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
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
    return json.loads(res)["results"]["bindings"]


def inferences(request):
    if request.method == 'POST':
        if 'spin' in request.POST:
            context = execute_spin()
            return render(request, 'inferences.html', context)
        
        if 'person_search' in request.POST:
            person = request.POST.get('person_type')
            person_class = ''
            prompt = ''
            match person:
                case 'Actor':
                    prompt += 'Actors'
                    person_class = "?person_id rdf:type sub:Actor ."
                case 'Director':
                    prompt += 'Directors'
                    person_class = "?person_id rdf:type sub:Director ."
                case 'AllPeople':
                    prompt += 'Everyone'
                    person_class = "?person_id rdf:type schema:Person ."

            results = inference_person(person_class)
            num_results = len(results)
            if num_results > 200:
                results = results[:200]
            return render(request, 'inferences.html', {'results_person': results, 'num_results': num_results, 'prompt': prompt})

        selected_type = request.POST.get('type')
        selected_rating = request.POST.get('rating')
        selected_duration = request.POST.get('duration')

        prompt = ''

        movOrShow = None  # False = movie, True = TV show, None = all

        if selected_type in ["Movie", "OldMovie", "RecentMovie"]:
            movOrShow = False
        elif selected_type in ["TVShow", "OldTVShow", "RecentTVShow"]:
            movOrShow = True

        if selected_duration in ["LongMovie", "ShortMovie"] and movOrShow:
            return render(request, 'inferences.html', {
                'error': 'Short Movie does not correspond to TV Shows',
                'selectedType': selected_type,
                'selectedRating': selected_rating,
                'selectedDuration': selected_duration
            })
        if selected_duration in ["LongTVShow", "ShortTVShow"] and movOrShow is False:
            return render(request, 'inferences.html', {
                'error': 'Long TV Show does not correspond to Movies',
                'selectedType': selected_type,
                'selectedRating': selected_rating,
                'selectedDuration': selected_duration
            })

        match selected_type:
            case "Media":
                movOrShow = None
                prompt += 'All Media '
                type_class = '?media rdf:type schema:Media .'
            case "Movie":
                movOrShow = False
                prompt += 'Movies '
                type_class = '?media rdf:type sub:Movie .'
            case "OldMovie":
                movOrShow = False
                prompt += 'Old movies '
                type_class = '?media rdf:type sub:OldMovie .'
            case "RecentMovie":
                movOrShow = False
                prompt += 'Recent movies '
                type_class = '?media rdf:type sub:RecentMovie .'
            case "TVShow":
                movOrShow = True
                prompt += 'TV Shows '
                type_class = '?media rdf:type sub:TVShow .'
            case "OldTVShow":
                movOrShow = True
                prompt += 'Old TV Shows '
                type_class = '?media rdf:type sub:OldTVShow .'
            case "RecentTVShow":
                movOrShow = True
                prompt += 'Recent TV Shows '
                type_class = '?media rdf:type sub:RecentTVShow .'

        match selected_rating:
            case "NoRating":
                rating = ''
            case "Kids":
                prompt += 'for kids '
                rating = '?media rdf:type sub:Kids .'
            case "Teens":
                prompt += 'for teens '
                rating = '?media rdf:type sub:Teens .'
            case "Adults":
                prompt += 'for adults '
                rating = '?media rdf:type sub:Adults .'

        match selected_duration:
            case "AllDuration":
                duration = ''
            case "LongMovie":
                prompt += 'that are long '
                duration = '?media rdf:type sub:LongMovie .'
            case "ShortMovie":
                prompt += 'that are short '
                duration = '?media rdf:type sub:ShortMovie .'
            case "LongTVShow":
                prompt += 'that are long '
                duration = '?media rdf:type sub:LongTVShow .'
            case "ShortTVShow":
                prompt += 'that are short '
                duration = '?media rdf:type sub:ShortTVShow .'

        results = inference_media(type_class, rating, duration)
        num_results = len(results)
        if num_results > 200:
            results = results[:200]
        return render(request, 'inferences.html', {'results': results, 'num_results': num_results, 'prompt': prompt})

        
    return render(request, 'inferences.html', {'num': 100})

def inference_media(type_class, rating, duration):
    query = """
        PREFIX schema: <https://schema.org/>
        PREFIX netflix: <http://ws.org/netflix_info/>
        PREFIX pred: <http://ws.org/netflix_info/pred/>
        PREFIX sub: <http://ws.org/netflix_info/sub/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX ex: <http://example.org/>

        SELECT ?type ?title ?director (GROUP_CONCAT(DISTINCT ?cast; separator=", ") AS ?mergedCasts)
                    ?country ?date_added ?release ?rating ?duration 
                    (GROUP_CONCAT(DISTINCT ?genres; separator=", ") AS ?mergedGenres) ?description
        WHERE {
            _type_class_
            _rating_
            _duration_
            
            ?media pred:title ?title_id .
            ?title_id pred:real_name ?title .
            
            ?media pred:duration ?duration_id .
            ?duration_id pred:real_name ?duration .
            
            ?media pred:cast ?cast_id .
            ?cast_id pred:real_name ?cast .
            
            ?media pred:director ?director_id .
            ?director_id pred:real_name ?director .
            
            ?media pred:release_year ?release_id .
            ?release_id pred:real_name ?release .
            
            ?media pred:description ?description_id .
            ?description_id pred:real_name ?description .
            
            ?media pred:type ?type_id .
            ?type_id pred:real_name ?type .
            
            ?media pred:country ?country_id .
            ?country_id pred:real_name ?country .
            
            ?media pred:date_added ?date_added_id .
            ?date_added_id pred:real_name ?date_added .
            
            ?media pred:rating ?rating_id .
            ?rating_id pred:real_name ?rating .
            
            ?media pred:listed_in ?genres_id .
            ?genres_id pred:real_name ?genres .
        } GROUP BY ?type ?title ?director ?country ?date_added ?release ?rating ?duration ?description
        """
    
    query = query.replace("_type_class_", type_class)
    query = query.replace("_rating_", rating)
    query = query.replace("_duration_", duration)
    
    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)    
    res = json.loads(res)

    mod_js =  transform_json(res['results']['bindings'])

    return mod_js

def inference_person(person_class):
    query = """
            PREFIX pred: <http://ws.org/netflix_info/pred/>
            PREFIX sub: <http://ws.org/netflix_info/sub/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX schema: <https://schema.org/>
            SELECT ?person
            WHERE {
                _class_
                ?person_id pred:real_name ?person .
            }
            """
    query = query.replace("_class_", person_class)

    payload_query = { "query": query }
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)    
    res = json.loads(res)

    mod_js = transform_json(res['results']['bindings'])

    return mod_js

def execute_spin():
    spin_rules = {""" PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>

INSERT {
  ?media a sub:Movie .
} WHERE {
  ?media a schema:Media .
  ?media pred:type ?type_id .
  ?type_id pred:real_name "Movie" .
}
""", 
"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>

INSERT {
  ?media a sub:TVShow .
} WHERE {
  ?media a schema:Media .
  ?media pred:type ?type_id .
  ?type_id pred:real_name "TV Show" .
} """, """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:Adults .
} WHERE {
  ?movie a schema:Media .
    ?movie pred:rating ?rating_id .
    ?rating_id pred:real_name ?rating .
    FILTER(?rating = "TV-14" || ?rating = "TV-MA" || ?rating = "R" || ?rating = "NC-17")
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:Kids .
} WHERE {
  ?movie a schema:Media .
    ?movie pred:rating ?rating_id .
    ?rating_id pred:real_name ?rating .
    FILTER(?rating = "TV-Y" || ?rating = "TV-G" || ?rating = "TV-PG" || ?rating = "G")
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:Teens .
} WHERE {
  ?movie a schema:Media .
    ?movie pred:rating ?rating_id .
    ?rating_id pred:real_name ?rating .
    FILTER(?rating = "TV-Y7" || ?rating = "TV-Y7-FV" || ?rating = "PG" || ?rating = "PG-13")
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:LongMovie .
} WHERE {
  ?movie a sub:Movie .
  ?movie pred:duration ?duration_id .
  ?duration_id pred:real_name ?duration .
  
  FILTER(xsd:integer(REPLACE(?duration, "[^0-9]", "")) > 90)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:LongTVShow .
} WHERE {
  ?movie a sub:TVShow .
  ?movie pred:duration ?duration_id .
  ?duration_id pred:real_name ?duration .
  
  FILTER(xsd:integer(REPLACE(?duration, "[^0-9]", "")) >= 2)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:ShortMovie .
} WHERE {
  ?movie a sub:Movie .
  ?movie pred:duration ?duration_id .
  ?duration_id pred:real_name ?duration .
  
  FILTER(xsd:integer(REPLACE(?duration, "[^0-9]", "")) <= 90)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:ShortTVShow .
} WHERE {
  ?movie a sub:TVShow .
  ?movie pred:duration ?duration_id .
  ?duration_id pred:real_name ?duration .
  
  FILTER(xsd:integer(REPLACE(?duration, "[^0-9]", "")) < 2)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:OldMovie .
} WHERE {
  ?movie a sub:Movie .
  ?movie pred:release_year ?release_year .
  ?release_year pred:real_name ?release .
  
  FILTER(xsd:integer(?release) < 2000)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:RecentMovie .
} WHERE {
  ?movie a sub:Movie .
  ?movie pred:release_year ?release_year .
  ?release_year pred:real_name ?release .
  
  FILTER(xsd:integer(?release) >= 2000)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:OldTVShow .
} WHERE {
  ?movie a sub:TVShow .
  ?movie pred:release_year ?release_year .
  ?release_year pred:real_name ?release .
  
  FILTER(xsd:integer(?release) < 2000)
}
""", """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sub: <http://ws.org/netflix_info/sub/>
PREFIX schema: <https://schema.org/>
PREFIX pred: <http://ws.org/netflix_info/pred/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
  ?movie a sub:RecentTVShow .
} WHERE {
  ?movie a sub:TVShow .
  ?movie pred:release_year ?release_year .
  ?release_year pred:real_name ?release .
  
  FILTER(xsd:integer(?release) >= 2000)
}
"""}
    
    for rule in spin_rules:
        response = sparql_update(rule, repo_name)
        if response.status_code == 200:
            return {'error': 'Failed to run SPIN rules: ' + response.text}
        
    return {'success': 'Successful loading of the SPIN rules. Run again to be sure everything is loaded.'}
