#!/usr/bin/env python3
from itertools import takewhile
import os
import sys
import posixpath
from urllib.parse import urlparse
import re
import cchardet as chardet
import argparse

# FIXME: need a better method than str.replace(), there are situations where it
# will accidentally replace the wrong text. For example having href-looking
# strings in user-facing text. (it would need the full domain and path, but is
# still possible to encounter) We should consider using a proper regex
# replacement here.
def write_subs(html, path, subs):
	for (old, new) in subs:
		html = html.replace(old, new, 1)
	with open(path, 'w') as outfile:
		outfile.write(html)
	print(f'Wrote {len(subs)} link substitutions to {path}')

def print_subs(filename, subs):
	print('{}:'.format(filename))
	for (oldstr, newstr) in subs:
		print('\t', oldstr, '->', newstr)

def read_file(path):
	with open(path, 'rb') as infile:
		content = infile.read()
		result = chardet.detect(content)
		charenc = result['encoding']
		return content.decode(charenc)

def is_html(filename):
	html_extensions = ['html', 'xhtml', 'htm']
	return filename.split('.')[-1].lower() in html_extensions

def relativize(home_domain, web_root_path, html_file_path, link_attr_value):
	"""
	:param home_domain: Domain that originally hosted the file
	:param web_root_path: Path of the web root on the local filesystem
	:param html_file_path: Path of html file containing the links we are working on
	:param link_attr_value: Link we will be relativizing (can be from href, src, etc)
	"""
	# link_attr_value can be in one of 3 formats:
	#
	# 1. domain-based absolute, eg https://www.example.com/foo/bar.html
	# 2. non-domain absolute, eg /foo/bar.html
	# 3. relative, eg foo/bar.html
	#
	# Our objective is to convert type (1) and (2) into type (3)

	# parse the url for easier handling
	url_parsed = urlparse(link_attr_value)

	# If this is an external link to another site, dont replace anything
	if url_parsed.netloc != home_domain:
		return link_attr_value

	# Strip the domain portion of the link and leading slash
	# This effectively converts link type 1. and 2. into 3.
	# eg example.com/foo/bar.html => foo/bar.html
	link_path = url_parsed.path.lstrip('/')

	# Where the link is relativized from, ie the directory of the HTML file
	# containing the link. If we are processing a link in
	# /tmp/example/index.html, this becomes /tmp/example
	link_cwd = posixpath.dirname(html_file_path)

	# join link_path with webroot, eg if webroot is /tmp/example/,
	# link_abs_path becomes /tmp/example/foo/bar.html
	link_abs_path = posixpath.join(web_root_path, link_path)

	# Return the relativized path
	relativized_path = posixpath.relpath(link_abs_path, link_cwd)

	# verify the relativized path we computed actually exists, otherwise return
	# original link value
	if posixpath.exists(link_abs_path):
		return relativized_path
	else:
		offending_file = posixpath.relpath(html_file_path, web_root_path)
		print(f"WARNING: Relative path missing on filesystem: '{offending_file}' links non-existant '{relativized_path}'")
		return link_attr_value

def get_html_files(root):
	""" Return a list of absolute paths of html files under root  """
	html_files = []
	for (dirpath, _, filenames) in os.walk(root):
		absify = lambda f: posixpath.join(dirpath, f)
		filenames = [f for f in filenames if is_html(f)]
		filenames = [absify(f) for f in filenames] 
		html_files.extend(filenames)
	return html_files

def get_links(html):
	""" Return a list of links from an html string"""
	return re.findall(r'(?:href|link|src)=["\'](.*?)["\']', html)

def get_subs(relativize_fn, links):
	""" Return a list of substitution pairs, where the first item is the
	original string (link) and the second item is the string to replace it
	(relativized link). Duplicate subs are filtered out."""
	subs = ((l, relativize_fn(l)) for l in links)
	subs = filter(lambda p: p[0] != p[1], subs) # filter out no-op substitutions
	return list(subs)

def main():
	parser = argparse.ArgumentParser(description='Convert absolute links to relative links in HTML files under a webroot')
	parser.add_argument('-p', metavar='webroot', required=True, help='Path to webroot directory containing HTML files')
	parser.add_argument('-d', metavar='domain', required=True, help='Domain used in absolute links to be made relative')
	parser.add_argument('-w', action='store_true', default=False, help='Write all link substutions to file(s)')
	parser.add_argument('-v', action='store_true', default=False, help='Verbose mode, print all link substutions')
	args = parser.parse_args(sys.argv[1:])

	# extract input values from args
	domain = args.d
	webroot = posixpath.abspath(args.p)
	verbose_mode = args.v
	write_mode = args.w

	# verify domain is an directory
	if not posixpath.isdir(webroot):
		print(f"ERROR: {webroot} is not a valid directory")
		quit(1)

	# get list of html file paths under webroot
	html_files = get_html_files(webroot)
	sub_count = 0

	for html_file in html_files:
		# get html string and link list
		html = read_file(html_file)
		links = get_links(html)
		
		# helper lambda to relativize path
		r = lambda link: relativize(domain, webroot, html_file, link)
		# get a list of link substitutions for this file
		subs = get_subs(r, links)
		sub_count += len(subs)

		# stop processing this html file if no subs are possible
		if len(subs) == 0:
			continue

		# if verbose, print the substitution pairs for this file
		if verbose_mode:
			print_subs(html_file, subs)

		# if write, save substitutions to file
		if write_mode:
			write_subs(html, html_file, subs)

	print(f"Found {sub_count} potential link substitutions in {len(html_files)} HTML files")
	if not verbose_mode and not write_mode:
		print("\tUse -v to list these changes or -w to write changes to disk")

main()
