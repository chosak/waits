from collections import namedtuple
from datetime import datetime, timedelta
from django.db.models import Min
from django.shortcuts import render

from transitfeeds.models import Query, RailPrediction

def waits(request, template_name):
	# Use only recent queries.
	end_time = datetime.now()
	start_time = end_time - timedelta(hours=1)
	recent = Query.objects.filter(created__range=(start_time, end_time))

	# Collect minimum waits for each recent query.
	waits_by_query = {}
	for query in recent:
		predictions = RailPrediction.objects.filter(query=query,
													destination_id__isnull=False,
													destination_name__isnull=False,
													line__isnull=False)
		min_waits = predictions.values('location_name', 'line', 'destination_name').annotate(min_wait=Min('wait'))
		offset = (query.created - start_time).total_seconds()
		waits_by_query[int(offset)] = min_waits

	# Organize data by route, where a route is a combination of location, group, and line.
	waits_by_route = {}
	Route = namedtuple('Route', ['location_name', 'line', 'destination_name'])
	for offset, query_waits in waits_by_query.iteritems():
		for route in query_waits:
			index = Route(route['location_name'],
						  route['line'],
						  route['destination_name'])
			if index not in waits_by_route:
				waits_by_route[index] = []
			waits_by_route[index].append({ 'offset': offset, 'wait': route['min_wait'] });

	waits_by_route = [(k,waits_by_route[k]) for k in sorted(waits_by_route.iterkeys())]
	return render(request, template_name, { 
		'waits': waits_by_route,
		'duration': (end_time - start_time).total_seconds() 
	})
