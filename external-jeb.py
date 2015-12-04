from bs4 import BeautifulSoup
import re

# Load a module page from a URL.
def get_module_page(url):
	# To be completed... right now open reference html locally.
	try:
		f = open(url, 'r')
	except IOError:
		return False
	return f.read()

# Given a BeautifulSoup object of a module page, find all the files.
def get_files(bs):
	links = bs.findAll('a')
	file_re = re.compile('.*\.pdf')
	for link in links:
		if file_re.match(str(link.get('href'))):
			print link.get('href')
	print "No. of links found: " + str(len(links))

if __name__ == '__main__':
	# Start by loading a module page into BeautifulSoup
	module = get_module_page('ref/module.html')
	if module:
		bs = BeautifulSoup(module, 'html.parser')
		# Get all the file URLs
		get_files(bs)
	else:
		print "Couldn't open file"
	
