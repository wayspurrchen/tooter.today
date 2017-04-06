from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.shortcuts import model_to_dict
import datetime

db = SqliteExtDatabase('tooters.db')

class BaseModel(Model):
	class Meta:
		database = db

class Instance(BaseModel):
	online = BooleanField(default=False)
	domain = CharField(unique=True)
	user_count = IntegerField()
	status_count = IntegerField()
	connected_instance_count = IntegerField()
	registration_open = BooleanField()
	uptime = FloatField()
	ipv6_support = BooleanField(null=True)
	https_score = TextField(null=True)
	short_about = TextField(null=True)
	long_about = TextField(null=True)
	last_updated = DateField()

db.connect()
db.create_tables([Instance], safe=True)

def store_instance(instance_data):
	existing = Instance.select().where(Instance.domain == instance_data['domain'])
	if existing.exists():
		print "Updating " + instance_data['domain'] + " in place"
		Instance.update(**instance_data).where(Instance.domain == instance_data['domain']).execute()
	else:
		print "Inserting new record for " + instance_data['domain']
		instance = Instance(**instance_data)
		instance.save()

def get_instances():
	query = Instance.select().where(
		Instance.online == True,
		Instance.registration_open == True
	)
	return [model_to_dict(c) for c in query]