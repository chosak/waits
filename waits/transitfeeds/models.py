from django.db import models
from stringfield import StringField

class Query(models.Model):
	provider_name = StringField()
	created = models.DateTimeField()
	success = models.BooleanField(default=False)

class RailPrediction(models.Model):
	query = models.ForeignKey(Query)

	location_id = StringField()
	location_name = StringField()
	group = models.IntegerField()
	
	line = StringField(null=True)
	destination_id = StringField(null=True)
	destination_name = StringField(null=True)
	minutes = StringField(null=True)
	cars = StringField(null=True)
	
	# Numeric value derived from minutes.
	wait = models.FloatField(null=True)
