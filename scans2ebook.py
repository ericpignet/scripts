#! /usr/bin/python

# scans2ebook.py
# Author: Eric Pignet
# 16/05/2012
# TODO
# - temporary files should be in /tmp
# - autodetect need to split: if more than 50% images are landscape

import os
import shlex, subprocess
import argparse
import urllib2
from bs4 import BeautifulSoup
import shutil

def postProcessImages():
	for root, dirs, files in os.walk('./'):
	    print root
	    print dirs
	    print files
	    #os.makedirs('../output/'+root)
	    for name in files:
		fullname = root + '/' + name
	        if name.endswith((".jpg", ".png", ".jpeg")):

			# For each image
			print ('Processing: ' + fullname)
	
			# Is the image in landscape format?
			if args.split == 'y':
				dimensions = subprocess.check_output(shlex.split('identify '+fullname)).split(" ")[2].split('x')
				if int(dimensions[0]) > int(dimensions[1]):
					# Landscape => split the image into two images
					print ' croping because '+dimensions[0]+'>'+dimensions[1]
					os.system('convert -crop 50%x100% \"' + fullname + '\" \"'+root+'/x' + os.path.splitext(name)[0] + '%d' + os.path.splitext(name)[1]+'\"') 
					# trim the images (and reverse order)
					os.system('convert -trim -fuzz 10% \"'+root+'/x' + os.path.splitext(name)[0] + '0' + os.path.splitext(name)[1] + '\" \"'+root+'/' + os.path.splitext(name)[0] + '1' + os.path.splitext(name)[1]+'\"')
					os.system('convert -trim -fuzz 10% \"'+root+'/x' + os.path.splitext(name)[0] + '1' + os.path.splitext(name)[1] + '\" \"'+root+'/' + os.path.splitext(name)[0] + '0' + os.path.splitext(name)[1]+'\"')
					# remove originals
					os.remove(root+'/x' + os.path.splitext(name)[0] + '0' + os.path.splitext(name)[1])
					os.remove(root+'/x' + os.path.splitext(name)[0] + '1' + os.path.splitext(name)[1])
				else:
					print ' no croping because '+dimensions[0]+'<'+dimensions[1]+', trim'
					# Trim the image
					os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"'+root+'/'+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')
			else:
				print ' trim'
				# Trim the image
				os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"'+root+'/'+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')
				os.remove(fullname)
				os.rename(root+'/'+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1], fullname)


################################
# Handle arguments
################################

parser = argparse.ArgumentParser(description='Process manga scans.')
parser.add_argument('manga', help='name of the manga to download')
parser.add_argument('-s', '--split', action='store_const', const='y', help='split the horizontal images into two vertical images')
parser.add_argument('-t', '--trim', action='store_const', const='y', help='trim white space around pages')

args = parser.parse_args()
#parser.print_help()
print args

################################
# Find list of volumes/chapters
################################

soup = BeautifulSoup(urllib2.urlopen('http://mangafox.me/manga/'+args.manga+'/').read())

manga = ''
volumes = {}

for link in soup.find_all('a'):
	if link.get('class') is not None and 'tips' in link.get('class'):
		href = link.get('href').split('/')
		if href[5] not in volumes:
			volumes[href[5]] = []
		volumes[href[5]].append([href[6], link.get('href')])
		manga = href[4]
print(volumes)

#os.system('rm -rf ../output')
#os.makedirs('../output')

################################
# Download each volume/chapter
################################

for volumename, chapters in volumes.iteritems():
	os.makedirs(manga+' '+volumename)
	os.chdir(manga+' '+volumename+'/')
	for chapter in chapters:
		print('Downloading')
		os.system('galleroob download '+chapter[1])
	postProcessImages()
	shutil.make_archive('../'+manga+' '+volumename, 'zip')
	os.chdir('..')
	os.rename(manga+' '+volumename+'.zip', manga+' '+volumename+'.cbz')
exit(0)

# Browse list of images

