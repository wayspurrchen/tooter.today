from lxml import html, etree
import requests
import threading
import time
from markdownify import markdownify as md

from host_db import store_instance

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.daemon = True
    t.start()
    return t

def gather_data_from_instances_xyz():
	page = requests.get('https://instances.mastodon.xyz/')
	tree = html.fromstring(page.content)
	rows = tree.cssselect('table.table tbody tr')
	props = []

	for row in rows:
		instance_data = {
			'domain': row.cssselect('th a')[0].get('href'),
			'user_count': row.cssselect('td')[1].text.strip(),
			'uptime': float(row.cssselect('td')[3].text.strip()[0:-1])
		}

		online = row.cssselect('td')[0].text.strip()
		instance_data['online'] = True if online.lower() == 'up' else False
		registration_open = row.cssselect('td')[2].text.strip()
		instance_data['registration_open'] = True if registration_open.lower() == 'yes' else False
		ipv6_support = row.cssselect('td')[5].text.strip()
		instance_data['ipv6_support'] = True if ipv6_support.lower == 'yes' else False

		potential_https = row.cssselect('td')[4].cssselect('a')
		if len(potential_https) > 0:
			instance_data['https_score'] = potential_https[0].text.strip()
		else:
			instance_data['https_score'] = ''

		instance_detail_page = None
		if instance_data['online']:
			try:
				instance_detail_page = requests.get(
					instance_data['domain'] + '/about/more',
					timeout=3
				)
			except:
				pass

		if instance_detail_page:
			detail_tree = html.fromstring(instance_detail_page.content)
			panel = detail_tree.cssselect('.main .panel')
			# the LIVE user count
			instance_data['user_count'] = int(
				detail_tree.cssselect('.information-board .section')[0]
					.cssselect('strong')[0].text.strip().replace(',', '')
			)
			instance_data['status_count'] = int(
				detail_tree.cssselect('.information-board .section')[1]
					.cssselect('strong')[0].text.strip().replace(',', '')
			)
			instance_data['connected_instance_count'] = int(
				detail_tree.cssselect('.information-board .section')[2]
					.cssselect('strong')[0].text.strip().replace(',', '')
			)
			if len(panel) > 0:
				panel_html = etree.tostring(panel[0])
				instance_data['long_about'] = md(panel_html)
			else:
				instance_data['long_about'] = None

		instance_data['last_updated'] = time.time()
		print "Storing instance data for " + instance_data['domain']
		print instance_data
		store_instance(instance_data)

def kickoff_host_gatherer():
	set_interval(gather_data_from_instances_xyz, 3600)

if __name__ == "__main__":
	gather_data_from_instances_xyz()
