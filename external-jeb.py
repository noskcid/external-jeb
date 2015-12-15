from bs4 import BeautifulSoup
import re
import requests
from requests.auth import HTTPBasicAuth
from os.path import isdir, dirname
from os import mkdir, makedirs
from urllib import unquote_plus
import getpass


# When in debug mode, avoids making requests, uses local copies instead.
debug = True

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
	# Removes an annoying urllib3 warning on every request. 
	# For the record, the warning is an InsecurePlatformWarning
	# "A true SSLContext object is not available"
	requests.packages.urllib3.disable_warnings()
	# Essentially, if in debug mode we don't need auth details (would get pretty
	# tiresome entering details everytime). Although first run of debug mode need
	# to download offline files to use.
	if debug:
		# Assume if no ref folder, the offline files need downloading.
		if not isdir('ref'):
			if not get_ref_debug_files():
				raise Exception # Eurgh so crude.
		auth = False
	else:
		auth = get_auth()
		
	# Module Page to scrape.
	base_url = "https://www.elec.york.ac.uk/internal_web/meng/yr4/modules/Sig_Proc/Theory_and_Practice/"

	# Local directory to save files.
	folder = 'downloads/SigProcTheory/'

	# Get Authorisation details.
	auth = get_auth()
	
	# Get module page.
	module_page = get_page(base_url, auth)
	if module_page:
		bs = BeautifulSoup(get_page(base_url, auth), 'html.parser')

		# Compile regular expression to find common file types.
		type_re = re.compile('.*\.(pdf|docx|doc|ppt)')

		# Get all the file URLs matching the regex.
		files = get_files(bs, type_re)

		print "Found {0} matching files.".format(len(files))
			
		# Download the files
		for f in files:
			# Get its URL
			rel_url = f.get('href')

			# Create the full URL
			url = base_url + rel_url

			filename = folder + rel_url
			lm = download_file(url, unquote_plus(filename), auth)
			if not lm:
				print "Download unsuccessful: " + url
	else:
		print "Could not download module page: " + base_url
