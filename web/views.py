#views.py

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render
from .models import *
from itertools import chain

import re

from django.db.models import Q

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def pdx(request, pk):
	pdx = PdxStrain.objects.get(pk=pk)
	return render(request, 'pdx.html', {'pdx': pdx})

def resources(request):
    return render(request, 'resources.html',)


def index(request):
    return render(request, 'home.html',)

def search(request):
    query_string = ''
    found_entries = None

    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']

        tumor_query = get_query(query_string, ['tumor_type', 'tissue_of_origin', 'diagnosis'])
        tumors = Tumor.objects.filter(tumor_query)

        marker_query = get_query(query_string, ['gene',])
        markers = Marker.objects.filter(marker_query)

        found_entries = list(chain(markers, tumors))

    return render(
		request,
		'search/search_results.html',
		{ 'query_string': query_string, 'found_entries': found_entries }, 
	)
