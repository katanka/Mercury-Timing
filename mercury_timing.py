from selenium import webdriver
from multiprocessing import Pool, Manager
import urllib2, json
import numpy as np
import matplotlib.pyplot as plt

wikiDomain = "gameofthrones"

random_url = "api.php?action=query&generator=random&grnnamespace=0&format=json"


workers = []
data = Manager().list()

total_calls = 15
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

def generateRandomURL():
	title = extractTitle(json.loads(urllib2.urlopen( generateURL(wikiDomain, random_url, False) ).read()))

	return generateURL(wikiDomain, 'wiki/' + title.replace(' ', '_'), True)

def generateURL(wikiDomain, localPath, noexternals):
	return 'http://' + wikiDomain + '.wikia.com/' + localPath + ('?noexternals=1' if noexternals else '')

def processRandomPage(url):
	print url
	

	size = len(urllib2.urlopen(url).read())
	

	mobile_emulation = { "deviceName": "Google Nexus 5" }
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

	driver = webdriver.Chrome(chrome_options=chrome_options)
	driver.get(url)

	start = driver.execute_script("return window.performance.timing.navigationStart")
	domContentLoadedEventTime = driver.execute_script("return window.performance.timing.domContentLoadedEventStart")
	loadEventTime = driver.execute_script("return window.performance.timing.loadEventStart")

	driver.close()

	domContentLoaded = domContentLoadedEventTime - start
	loadEvent = loadEventTime - start

	if (domContentLoaded > 0) and (loadEvent > 0):
		return {
			'url': url,
			'size': size,
			'domContentLoaded': domContentLoaded,
			'loadEvent': loadEvent
		}

pool = Pool(processes=10)              # start 4 worker processes
urls = [generateRandomURL() for _ in range(total_calls)]
data = pool.map(processRandomPage, urls)
# while current_calls < total_calls:
# 	while current_workers < max_workers:
#         p = Process(target=processRandomPage, args=(data,))
#         workers.append(p)
#         p.start()
#         current_workers += 1

for obj in data:
	print obj

N = len(data)
size = [page['size'] for page in data]
domContentLoaded = [page['domContentLoaded'] for page in data]
loadEvent = [page['loadEvent'] for page in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_xlabel('Size (bytes)')
ax.set_ylabel('Time (ms)')
ax.axis([min(size) - 10000, max(size) + 10000, 0, max(loadEvent)+1000])


ax.scatter(size, loadEvent, label='loadEvent', color='red')
ax.scatter(size, domContentLoaded, label='domContentLoaded')

plt.legend(loc='upper left')
plt.show()
