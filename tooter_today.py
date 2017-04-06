#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import render_template
app = Flask(__name__)

import random
from gather_host_data import kickoff_host_gatherer
from host_db import get_instances
from markdown2 import markdown

# http://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another
def translate(value, toMin, toMax, fromMin, fromMax):
    # Figure out how 'wide' each range is
    toSpan = toMax - toMin
    fromSpan = fromMax - fromMin

    # Convert the to range into a 0-1 range (float)
    valueScaled = float(value - toMin) / float(toSpan)

    # Convert the 0-1 range into a value in the from range.
    return fromMin + (valueScaled * fromSpan)

def score_instances():
	'''
	Instance selection algorithm

	Core score driven by ipv6 support and 
	https rating.

	https rating:
	A+ = 3
	A = 2
	B = 1
	F = 0
	other = 1

	IPV6 = 1

	long_about present = 1
	long_about longer than 140 characters = 1

	Core score is the sum of the above.

	The core score is then multiplied by the
	uptime (uptime * 0.01 to get 1.0 float)
	and shoved into this formula for exponential
	shittiness based on uptime: 2^x - 1

	so then: core score / 2^x - 1
	greater x = lower score

	then we multiply by the 
	'''
	instances = get_instances()

	least_users = 0
	most_users = 0

	for instance in instances:
		if instance['user_count'] > most_users:
			most_users = instance['user_count']

	for instance in instances:
		https_score = instance['https_score']
		score = 1
		https_score_map = {
			'A+': 3,
			'A': 2,
			'B': 1,
			'F': 0
		}

		# Start score based off https
		if https_score in https_score_map:
			score += https_score_map[https_score]

		if instance['long_about']:
			if len(instance['long_about']) > 140:
				score += 2
			else:
				score += 1

		if instance['ipv6_support']:
			score += 1

		# print instance['domain']

		uptime_modifier = pow(2, instance['uptime'] * 0.01)
		score *= uptime_modifier

		# parabolic curve so that instances with hella low
		# users aren't as likely to be suggested
		# ((x - 1)^2) / 4
		user_count_modifier = (
			pow(instance['user_count'] - 60.000000, 2.0) / 80.0
		) + 1

		# print '============='
		# print 'user count: ' + str(instance['user_count'])
		# print 'user count modifier: ' + str(user_count_modifier)
		# print 'core score: ' + str(score)
		# print 'final score w/ user_count_modifier: ' + str(score / user_count_modifier)

		instance['final_score'] = float(score / user_count_modifier)
		# print 'final score'

	return sorted(instances, key=lambda k: k['final_score'], reverse=True)

scored_instances = score_instances()

maybe_text = [
	'How about...',
	'I suggest...',
	'Maybe this is a fit...',
	'Hope this one looks good...',
	'What do you think of...',
	'Might be promising...'
]

again_text = [
	'Try again!',
	'Give me another one!',
	'Nah, how about...',
	'OK, interesting, but...',
	'Next one, please!',
	'That one was fine but...',
	'Give me more options!',
	'Something else, please!'
]

emoji = [
	u'🐢',
	u'🐘',
	u'🐳',
	u'🐋',
	u'🐊',
	u'🌞',
	u'🌛',
	u'🌜',
	u'🍏',
	u'🍎',
	u'🍐',
	u'🍊',
	u'🍋',
	u'🍌',
	u'🍉',
	u'🍇',
	u'🍓',
	u'🍈',
	u'🍒',
	u'🍑',
	u'🍍',
	u'🌅',
	u'🌄',
	u'🌠',
	u'🎇',
	u'🎆',
	u'🌇',
	u'🌆',
	u'🌃'
]

@app.route("/")
def home():
	instance = scored_instances[0]

	if instance['long_about']:
		instance['long_about'] = markdown(instance['long_about'])

	return render_template(
		'main.html',
		maybe_text=random.choice(maybe_text),
		again_text=random.choice(again_text),
		recommended_instance=instance,
		next_suggestion_index=1,
		emoji=random.choice(emoji)
	)

@app.route("/suggestions/<offset>")
def suggestion(offset=0):
	instance = scored_instances[int(offset)]
	if instance['long_about']:
		instance['long_about'] = markdown(instance['long_about'])

	return render_template(
		'main.html',
		maybe_text=random.choice(maybe_text),
		again_text=random.choice(again_text),
		recommended_instance=instance,
		next_suggestion_index=int(offset) + 1,
		emoji=random.choice(emoji)
	)

if __name__ == "__main__":
	app.run()
