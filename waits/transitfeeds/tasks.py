import json
import logging
import urllib2

from celery.task import periodic_task
from datetime import datetime, timedelta
from django.conf import settings

from transitfeeds.models import Query, RailPrediction

def get_feed_data(provider_name, url_pattern):
	api_key = ()

	if provider_name in dict(settings.TRANSITFEED_API_KEYS):
		api_key = dict(settings.TRANSITFEED_API_KEYS)[provider_name]

	query_time = datetime.now()
	query = Query(provider_name=provider_name, created=query_time)
	query.save()
		
	try:
		url = url_pattern % api_key
		response = urllib2.urlopen(url_pattern % api_key)
		data = response.read()
	except Exception as ex:
		logging.error('Caught exception querying transit feed: %s' % ex)
		raise

	query.success = True
	query.save()		

	return data, query

@periodic_task(run_every=timedelta(seconds=30), ignore_result=True)
def get_WMATA_rail_predictions():

	data, query = get_feed_data('WMATA', 'http://api.wmata.com/StationPrediction.svc/json/GetPrediction/All?api_key=%s')
	json_data = json.loads(data)
	
	for train in json_data['Trains']:
		prediction = RailPrediction(
			query=query,
			location_id=train['LocationCode'],
			location_name=train['LocationName'],
			group=train['Group'],
			line=train['Line'],
			destination_id=train['DestinationCode'],
			destination_name=train['Destination'],
			minutes=train['Min'],
			cars=train['Car'])

		try:
			prediction.wait = int(prediction.minutes)
		except:
			if prediction.minutes == 'BRD':
				prediction.wait = 0
			elif prediction.minutes == 'ARR':
				prediction.wait = 0.5
			else:
				prediction.wait = None

		prediction.save()
