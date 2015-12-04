from bs4 import BeautifulSoup
import re
import requests
from requests.auth import HTTPBasicAuth
from os.path import isdir
from os import mkdir
import getpass

# When in debug mode, avoids making requests, uses local copies instead.
debug = True

# Load a module page from a URL.
def get_module_page(url):
	if debug:
		# To be completed... right now open reference html locally.
		try:
			f = open(url, 'r')
		except IOError:
			return False
		return f.read()
	else:
		return False

# Given a BeautifulSoup object of a module page, find all the files.
def get_files(bs):
	links = bs.findAll('a')
	file_re = re.compile('.*\.pdf')
	for link in links:
		# Check whether it links to file type of interest.
		if file_re.match(str(link.get('href'))):
			print link.get('href')
	print "No. of links found: " + str(len(links))

# Retrieve a live page.
def get_page(url, auth):
	r = requests.get(url, auth=auth)
	if r.status_code == 200:
		return r.text
	else:
		if r.status_code == 401:
			print "Authentication failed"
		elif r.status_code == 404:
			print "Page not found"
		return False

# Get username and password for authentication.
def get_auth():
	username = raw_input('Username: ')
	password = getpass.getpass('Password: ')
	return (username,password)

# If in debug mode, download ref files for offline testing. 
def get_ref_debug_files():
	# For now we just need to get. dat. module. page (sig proc)
	auth = get_auth()
	p = get_page("https://www.elec.york.ac.uk/internal_web/meng/yr4/modules/Sig_Proc/Theory_and_Practice/", auth)
	if not p:
		return False
	# Make the ref directory
	try:
		mkdir('ref')
	except:
		return False
	f = open('ref/module.html','w')
	f.write(p)
	return True


if __name__ == '__main__':
	# Essentially, if in debug mode we don't need auth details (would get pretty
	# tiresome entering details everytime). Although first run of debug mode need
	# to download offline files to use.
	if debug:
		# Assume if no ref folder, the offline files need downloading.
		if not isdir('ref'):
			if not get_ref_debug_files():
				raise Exception # Eurgh so crude. 
	else:
		auth = get_auth()
		
	# Start by loading a module page into BeautifulSoup.
	module = get_module_page('ref/module.html')
	if module:
		bs = BeautifulSoup(module, 'html.parser')
		# Get all the file URLs
		get_files(bs)
	else:
		print "Couldn't open file"
	
