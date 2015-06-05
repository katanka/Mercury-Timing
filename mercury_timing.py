from selenium import webdriver
from multiprocessing import Pool, Manager
import urllib2, json, sys
from time import sleep
import numpy as np
import matplotlib.pyplot as plt

wikiDomain = "gameofthrones"

random_url = "api.php?action=query&generator=random&grnnamespace=0&format=json"


workers = []
data = Manager().list()

total_calls = 20
current_calls = 0
max_workers = 5
current_workers = 0

def extractTitle(data):
	title = ""

	if isinstance(data, dict):
		for key, val in data.iteritems():
			if key == 'title':
				title = val
				break
			elif isinstance(val, dict):
				title = extractTitle(val) if title == "" else title
			elif isinstance(val, list):
				title = extractTitle(val) if title == "" else title
	else:
		for val in data:
			title = extractTitle(val) if title == "" else title

	return title

def generateRandomURL(x):
	title = extractTitle(json.loads(urllib2.urlopen( generateURL(wikiDomain, random_url, False) ).read()))

	return generateURL(wikiDomain, 'wiki/' + title.replace(' ', '_'), True)

def generateURL(wikiDomain, localPath, noexternals):
	return 'http://' + wikiDomain + '.wikia.com/' + localPath + ('?noexternals=1' if noexternals else '')

def processRandomPage(url):
	

	size = len(urllib2.urlopen(url).read())
	

	mobile_emulation = { "deviceName": "Google Nexus 5" }
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

	driver = webdriver.Chrome(chrome_options=chrome_options)
	driver.get(url)

	start = driver.execute_script("return window.performance.timing.navigationStart")
	domContentLoadedEventTime = driver.execute_script("return window.performance.timing.domContentLoadedEventStart")
	loadEventTime = driver.execute_script("return window.performance.timing.loadEventStart")

	driver.quit()

	domContentLoaded = domContentLoadedEventTime - start
	loadEvent = loadEventTime - start

	if (domContentLoaded > 0) and (loadEvent > 0):
		return {
			'url': url,
			'size': size,
			'domContentLoaded': domContentLoaded,
			'loadEvent': loadEvent
		}


def waitMessage():
	i = 0
	while True:
	    if result.ready():
	        break
	    else:
	        sys.stdout.write('\r'+'.'*(i%3 + 1) + ' '*(2-i%3))
	        i += 1
	        sleep(1)
	        sys.stdout.flush()
	sys.stdout.write('\rDone\n')

if __name__ == "__main__":
	try:
		print 'Starting pool...'
		pool = Pool(processes=5)              # start 5 worker processes
		print 'Done'
		print 'Getting random urls...'

		result = pool.map_async(generateRandomURL, range(total_calls))

		# monitor loop
		waitMessage()

		urls = result.get()

		print 'Starting testing...'
		result = pool.map_async(processRandomPage, urls)

		waitMessage()

		data = result.get()

		print 'Starting result processing...'


		N = len(data)
		size = [page['size']/1000 for page in data]
		domContentLoaded = [page['domContentLoaded'] for page in data]
		loadEvent = [page['loadEvent'] for page in data]

		print 'Done'
		print 'Displaying plot'

		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.set_xlabel('Size (kb)')
		ax.set_ylabel('Time (ms)')
		ax.set_xscale('log')
		ax.axis([min(size)/2, max(size)*2, 0, max(loadEvent)+1000])


		ax.scatter(size, loadEvent, label='loadEvent', color='red', alpha=0.5)
		ax.scatter(size, domContentLoaded, label='domContentLoaded', alpha=0.5)

		plt.legend(loc='upper left')
		plt.show()
	except Exception as e:
		print e
