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
		waits_by_query[query.created] = min_waits

	# Organize data by route, where a route is a combination of location, group, and line.
	waits_by_route = {}
	Route = namedtuple('Route', ['location_name', 'line', 'destination_name'])
	for query_time, query_waits in waits_by_query.iteritems():
		for route in query_waits:
			index = Route(route['location_name'],
						  route['line'],
						  route['destination_name'])
			if index not in waits_by_route:
				waits_by_route[index] = {}
			waits_by_route[index][query_time] = route['min_wait'] 

	waits_by_route = [(k,waits_by_route[k]) for k in sorted(waits_by_route.iterkeys())]
	return render(request, template_name, { 'waits': waits_by_route })

	predictions = RailPrediction.objects.filter(query__in=recent, destination_id__isnull=False, destination_name__isnull=False, line__isnull=False).order_by(
		'location_name', 
		'group', 
		'line')

	combinations = predictions.values('location_name', 'group', 'line').distinct()
	
	for combination in combinations:
		location_name = combination['location_name']
		group = combination['group']
		line = combination['line']

		combination_predictions = predictions.filter(location_name=location_name,
													 group=group,
													 line=line)
		
		if not combination_predictions:
			continue
	
		destinations = combination_predictions.values('destination_name').distinct()
		destinations = [destination['destination_name'] for destination in destinations]

		wait_times = []
		for query in recent:
			min_wait = combination_predictions.filter(query=query).aggregate(Min('wait'))
			min_wait = min_wait['wait__min']	
		
			if min_wait is not None:
				wait_times.append(str(min_wait))
			else:
				wait_times.append('null')

		wait = {'location_name': location_name,
				'line': line,
				'group': group,
				'destinations': ', '.join(destinations),
				'wait_times': ','.join(wait_times) }
		waits.append(wait)
	
	return render(request, template_name, { 'waits': waits })
