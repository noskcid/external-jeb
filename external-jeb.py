from bs4 import BeautifulSoup
import re
import requests
from requests.auth import HTTPBasicAuth
from os.path import isdir, dirname, exists, getmtime
from os import mkdir, makedirs
from urllib import unquote_plus
import getpass
import argparse
from datetime import datetime
from sys import exit

# Load a module page from a URL.
def get_module_page(url, auth):
	if debug:
		# To be completed... right now open reference html locally.
		try:
			f = open(url, 'r')
		except IOError:
			return False
		return f.read()
	else:
		return get_page(url, auth)

# Download the file from the given url to the file given by filename. 
def download_file(url, filename, auth):
	
	r = requests.get(url, auth=auth, stream=True)
	
	if r.status_code == 200:
		if exists(filename):
			# Keep an eye on this, subject to change.
			strp_string = '%a, %d %b %Y %H:%M:%S %Z'
			last_mod = r.headers['Last-Modified']

			# Date the file was last updated on the server.
			online_date = datetime.strptime(last_mod, strp_string)

			# Date the file was last modified locally.
			local_date = datetime.fromtimestamp(getmtime(filename))

			if local_date > online_date:
				print "Local file up to date: " + filename
				return False
			else:
				print "New version available."

		try:
			f = open(filename, 'wb')
		except IOError:
			# Assume this is because the directory doesn't exist.
			try:
				# Make the directory.
				makedirs(dirname(filename))
				# Try again.
				f = open(filename, 'wb')
			except IOError:
				return False
		chunk_size = 512
		file_size = int(r.headers['Content-Length'])
		# Cheeky little line to ensure %complete not greater than 100%
		(q,rem) = divmod(file_size, chunk_size)
		if rem > 0:
			file_size = (q + 1) * chunk_size 
		completed = 0
		for chunk in r.iter_content(chunk_size=chunk_size):
			f.write(chunk)
			completed = completed + chunk_size
			progress = (float(completed) / float(file_size))*100
			print '\r{0} [{1}] {2:.1f}%'.format(filename, '#'*(int(progress/10)), progress),
		f.close()
		print '\n',
		return True
	else:
		return False



def file_get_last_modified(url, auth):
	r = requests.get(url, auth=auth, stream=True)
	if r.status_code == 200:
		return r.headers['Last-Modified']

# Given a BeautifulSoup object of a module page, find all the files whose
# url matches the regex.
def get_files(bs, type_re):
	links = bs.findAll('a')
	files = []
	for link in links:
		# Check whether it links to file type of interest.
		if type_re.match(str(link.get('href'))):
			files.append(link)
	return files

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


if __name__ == '__main__':
	# Removes an annoying urllib3 warning on every request. 
	# For the record, the warning is an InsecurePlatformWarning
	# "A true SSLContext object is not available"
	requests.packages.urllib3.disable_warnings()

	parser = argparse.ArgumentParser(prog='external-jeb')
	parser.add_argument('url', metavar='url', help='URL of page to retrieve files from')
	parser.add_argument('-o', metavar='output_folder', help='Output folder for downloaded files', default='')
	parser.add_argument('ext', nargs='*', help='Extentions to search (default pdf)', default=['pdf'])
	args = parser.parse_args()

	types_re_list = args.ext[0]
	for ext in args.ext[1:]:
		types_re_list = types_re_list + '|' + ext

	# Module Page to scrape.
	base_url = dirname(args.url)

	# Local directory to save files.
	folder = args.o

	# Get Authorisation details.
	auth = get_auth()
	
	# Get module page.
	module_page = get_page(args.url, auth)
	if module_page:
		bs = BeautifulSoup(module_page, 'html.parser')

		# Compile regular expression to find file types.
		type_re = re.compile('.*\.('+types_re_list+')')

		# Get all the file URLs matching the regex.
		files = get_files(bs, type_re)

		print "Found {0} matching files.".format(len(files))
			
		# Download the files
		for f in files:
			# Get its URL
			rel_url = f.get('href')

			# Create the full URL
			url = base_url + '/' + rel_url

			filename = folder + rel_url
			lm = download_file(url, unquote_plus(filename), auth)
			if not lm:
				print "Download unsuccessful: " + url
	else:
		print "Could not download module page: " + base_url
