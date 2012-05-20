#! /usr/bin/python

# scans2ebook.py
# Author: Eric Pignet
# 16/05/2012
# TODO
# - autodetect need to split: if more than 50% images are landscape
# - make it site-agnostic (would work with set of URLs and ask for volume information)
# - 2 independant phases: download and processing/packaging
# - change name of output directory to support parall runs in same directory
# - use weboob python module => download image by image?
# - display useful output, including progress bar for download

import os
import shlex, subprocess
import argparse
import urllib2
from bs4 import BeautifulSoup
import shutil
import re

def postProcessImages(volume):
	os.system('rm -rf ../output')
	os.makedirs('../output')
	for root, dirs, files in os.walk('./'):
		print dirs
		print files
		if len(root.split(' ')) ==3:
			chapter = root.split(' ')[2]+'_'
			print('Chapter: '+chapter)
		#os.makedirs('../output/'+root)
		for name in files:
			fullname = root + '/' + name
		        if name.endswith((".jpg", ".png", ".jpeg")):

				# For each image
				print ('Processing: ' + fullname)
	
				# Is the image in landscape format?
				if args.split == 'y':
					dimensions = subprocess.check_output(shlex.split('identify -format \'%wx%h\' \"'+fullname+'\"')).split('x')
					if int(dimensions[0]) > int(dimensions[1]):
						# Landscape => split the image into two images
						print ' croping because '+dimensions[0]+'>'+dimensions[1]
						os.system('convert -crop 50%x100% \"'+fullname+'\" \"../output/x'+chapter+os.path.splitext(name)[0]+'%d'+os.path.splitext(name)[1]+'\"') 
						# trim the images (and reverse order)
						os.system('convert -trim -fuzz 10% \"../output/x'+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\" \"../output/'+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1]+'\"')
						os.system('convert -trim -fuzz 10% \"../output/x'+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1]+'\" \"../output/'+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')
						# remove originals
						os.remove('../output/x'+chapter+os.path.splitext(name)[0] + '0' + os.path.splitext(name)[1])
						os.remove('../output/x'+chapter+os.path.splitext(name)[0] + '1' + os.path.splitext(name)[1])
					else:
						print ' no croping because '+dimensions[0]+'<'+dimensions[1]+', trim'
						if args.trim == 'y':
							# Trim the image
							os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"../output/'+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')
				else:
					if args.trim == 'y':
						print ' trim'
						# Trim the image
						os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"../output/'+chapter+name+'\"')
					else:
						shutil.copyfile(fullname, '../output/'+chapter+name)


################################
# Handle arguments
################################

parser = argparse.ArgumentParser(description='Process manga scans.')
parser.add_argument('manga', help='name of the manga to download')
parser.add_argument('-nd', '--no-download', action='store_true', help='skip the download phase, assumes files are already here')
parser.add_argument('-np', '--no-processing', action='store_true', help='skip the processing phase, download scans only')
parser.add_argument('-s', '--split', action='store_const', const='y', help='split the horizontal images into two vertical images')
parser.add_argument('-t', '--trim', action='store_const', const='y', help='trim white space around pages')
parser.add_argument('-k', '--keep', action='store_const', const='y', help='don\'t remove original downloaded files')
parser.add_argument('--from', action='store', dest='volfrom', help='number of first volume to download')
parser.add_argument('--to', action='store', dest='volto', help='number of last volume to download')

args = parser.parse_args()
#print args

################################
# Find list of volumes/chapters
################################

soup = BeautifulSoup(urllib2.urlopen('http://mangafox.me/manga/'+args.manga+'/').read())

manga = ''
volumes = {}

for link in soup.find_all('a'):
	if link.get('class') is not None and 'tips' in link.get('class'):
		href = link.get('href').split('/')
		# Keep only chapters belonging to volumes selected with arguments
		if args.volfrom <> None or args.volto <> None:
			volnumber = int(re.search('\d+', href[5]).group(0))
			if args.volfrom <> None and volnumber < int(args.volfrom):
				continue
			if args.volto <> None and volnumber > int(args.volto):
				continue
		if href[5] not in volumes:
			volumes[href[5]] = []
		volumes[href[5]].append([href[6], link.get('href')])
		manga = href[4]
print(volumes)

#os.makedirs('../output')

################################
# Download each volume/chapter
################################

summary = ''
for volumename, chapters in volumes.iteritems():
	os.makedirs(manga+' '+volumename)
	os.chdir(manga+' '+volumename+'/')
	incomplete = False
	for chapter in chapters:
		print('Downloading volume '+volumename+', chapter '+chapter[0])
		weboob_output = subprocess.check_output(shlex.split('galleroob download '+chapter[1]), stderr=subprocess.STDOUT)
		if 'Couldn\'t get page' in weboob_output:
			#retry 1st time
			print('Error, first retry')
			os.system('rm -rf \"'+manga+' '+volumename+' '+chapter[0]+'\"')
			weboob_output = subprocess.check_output(shlex.split('galleroob download '+chapter[1]), stderr=subprocess.STDOUT)
			if 'Couldn\'t get page' in weboob_output:
				#retry 2nd time
				print('Error, second retry')
				os.system('rm -rf \"'+manga+' '+volumename+' '+chapter[0]+'\"')
				weboob_output = subprocess.check_output(shlex.split('galleroob download '+chapter[1]), stderr=subprocess.STDOUT)
				if 'Couldn\'t get page' in weboob_output:
					summary = summary + '\nVolume '+volumename+' could not be downloaded'
					incomplete = True
					break
	if incomplete:
		continue
	postProcessImages(volumename)
	print('Compress in '+manga+' '+volumename+'.cbz')
	os.chdir('../output')
	shutil.make_archive('../'+manga+' '+volumename, 'zip')
	os.chdir('..')
	os.rename(manga+' '+volumename+'.zip', manga+' '+volumename+'.cbz')
print(summary)
