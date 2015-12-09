from bs4 import BeautifulSoup
import re
import requests
from requests.auth import HTTPBasicAuth
from os.path import isdir, dirname
from os import mkdir, makedirs
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

# Given a BeautifulSoup object of a module page, find all the files.
def get_files(bs):
	links = bs.findAll('a')
	file_re = re.compile('.*\.pdf')
	files = []
	for link in links:
		# Check whether it links to file type of interest.
		if file_re.match(str(link.get('href'))):
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
		
	# Start by loading a module page into BeautifulSoup.
	module = get_module_page('ref/module.html',auth)
	if module:
		bs = BeautifulSoup(module, 'html.parser')
		base_url = "https://www.elec.york.ac.uk/internal_web/meng/yr4/modules/Sig_Proc/Theory_and_Practice/"
		# Get all the file URLs
		files = get_files(bs)
		
		# Get the last file
		last = files.pop()
		
		# Get its URL
		rel_url = last.get('href')

		# Create the full URL
		url = base_url + rel_url
		
		# Get Authorisation details
		auth = get_auth()
		
		# Download the file
		filename = 'downloads/' + rel_url
		lm = download_file(url, filename, auth)
		if lm:
			print "Successfully downloaded to: " + filename
		else:
			print "Download unsuccessful."

	else:
		print "Couldn't open file"
	
