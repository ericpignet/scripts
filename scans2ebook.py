#! /usr/bin/python

# scans2ebook.py
# Process manga scans. By default, download the manga scans, split the horizontal pages, trim the white margins, create .cbz files, and remove the downloaded scans.
#
# Author: Eric Pignet
# 16/05/2012
# TODO
# - make it site-agnostic (would work with set of URLs and ask for volume information)
# - 2 independant phases: download and processing/packaging
# - change name of output directory to support parall runs in same directory
# - use weboob python module => download image by image?

import os
import shlex, subprocess
import argparse
import urllib2
from bs4 import BeautifulSoup
import shutil
import re
import sys	# for sys.stdout.write
import random

def postProcessImages(volume):
	shutil.rmtree(outputdir)
	os.makedirs(outputdir)
	for root, dirs, files in os.walk('./'):
		if args.debug:
			print dirs
			print files
		if len(root.split(' ')) ==3:
			chapter = root.split(' ')[2]+'_'
			print('Chapter: '+chapter)
		else:
			continue

		# Auto-detect default format for this chapter
		split = False
		if args.split == 'auto':
			nb_horizontal = 0
			nb_vertical = 0
			for name in files:
				fullname = root + '/' + name
			        if name.endswith((".jpg", ".png", ".jpeg")):
					dimensions = subprocess.check_output(shlex.split('identify -format \'%wx%h\' \"'+fullname+'\"')).split('x')
					if int(dimensions[0]) > int(dimensions[1]):
						nb_horizontal += 1
					else:
						nb_vertical += 1
			if nb_horizontal > ( 2 * nb_vertical):
				print('Auto-detection: split needed')
				split = True
			else:
				print('Auto-detection: split not needed')
		elif args.split == 'y':
			split = True

		# Process images	
		for name in files:
			fullname = root + '/' + name
		        if name.endswith((".jpg", ".png", ".jpeg")):

				# For each image
				sys.stdout.write('Processing: ' + fullname)
	
				# Is the image in landscape format?
				if split:
					dimensions = subprocess.check_output(shlex.split('identify -format \'%wx%h\' \"'+fullname+'\"')).split('x')
					if int(dimensions[0]) > int(dimensions[1].rstrip()):
						# Landscape => split the image into two images
						sys.stdout.write(' [split because '+dimensions[0]+'>'+dimensions[1].rstrip()+']')
						os.system('convert -crop 50%x100% \"'+fullname+'\" \"'+outputdir+'x'+chapter+os.path.splitext(name)[0]+'%d'+os.path.splitext(name)[1]+'\"') 

						if not args.trim:
							# reverse order
							sys.stdout.write('\n')
							os.rename(outputdir+'x'+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1], outputdir+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1])
							os.rename(outputdir+'x'+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1], outputdir+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1])
						else:
							# trim the images (and reverse order)
							sys.stdout.write(' [trim]\n')
							os.system('convert -trim -fuzz 10% \"'+outputdir+'x'+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\" \"'+outputdir+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1]+'\"')
							os.system('convert -trim -fuzz 10% \"'+outputdir+'x'+chapter+os.path.splitext(name)[0]+'1'+os.path.splitext(name)[1]+'\" \"'+outputdir+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')

						# remove originals
						os.remove(outputdir+'x'+chapter+os.path.splitext(name)[0] + '0' + os.path.splitext(name)[1])
						os.remove(outputdir+'x'+chapter+os.path.splitext(name)[0] + '1' + os.path.splitext(name)[1])
					else:
						sys.stdout.write(' [no split because '+dimensions[0]+'<'+dimensions[1].rstrip()+']')
						if args.trim:
							# Trim the image
							sys.stdout.write(' [trim]\n')
							os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"'+outputdir+chapter+os.path.splitext(name)[0]+'0'+os.path.splitext(name)[1]+'\"')
				else:
					if args.trim:
						sys.stdout.write(' [trim]\n')
						# Trim the image
						os.system('convert -trim -fuzz 10% \"'+fullname+'\" \"'+outputdir+chapter+name+'\"')
					else:
						shutil.copyfile(fullname, outputdir+chapter+name)
		if not args.keep:
			shutil.rmtree(root)

################################
# Handle arguments
################################

parser = argparse.ArgumentParser(prog='scans2ebook', description='Process manga scans. By default, %(prog)s will download the manga scans, split the horizontal pages, trim the white margins, create .cbz files, and remove the downloaded scans.')
parser.add_argument('manga', help='name of the manga to download')
#parser.add_argument('-nd', '--no-download', action='store_true', help='skip the download phase, assumes files are already here')
#parser.add_argument('-np', '--no-processing', action='store_true', help='skip the processing phase, download scans only')
parser.add_argument('--from', action='store', dest='volfrom', help='number of first volume to download')
parser.add_argument('--to', action='store', dest='volto', help='number of last volume to download')
parser.add_argument('--split', choices=['auto','y','n'], action='store', default='auto', help='split the horizontal images into two vertical images (default: %(default)s)')
parser.add_argument('--no-trim', action='store_false', dest='trim', help='do\'nt trim white space around pages')
parser.add_argument('-k', '--keep', action='store_true', help='don\'t remove original downloaded files')
parser.add_argument('--max-retry', action='store', dest='maxretry', default='3', help='max number of retries in case of download failure (default: %(default)s)')
parser.add_argument('--debug', action='store_true', help='display debug information')

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
if args.debug:
	print(volumes)

#os.makedirs('../output')
outputdir = '../output_'+manga+'_'+str(random.randint(0, 99999))+'/'

################################
# Download each volume/chapter
################################

summary = ''
for volumename, chapters in volumes.iteritems():
	os.makedirs(manga+' '+volumename)
	os.chdir(manga+' '+volumename+'/')
	chapter_incomplete = True
	for chapter in chapters:
		print('Downloading volume '+volumename+', chapter '+chapter[0]+' with Weboob')
		chapter_incomplete = True
		# We try to donwload a few times
		for i in range(int(args.maxretry)+1):
			p = subprocess.Popen(shlex.split('galleroob download '+chapter[1]), stderr = subprocess.PIPE)
			(out, weboob_output) = p.communicate()
			if 'Couldn\'t get page' in weboob_output:
				if i < (int(args.maxretry)+1):
					print('Error, retry nb '+ str(i+1))
				else:
					print ('Error, I\'m done retrying :-(')
				shutil.rmtree(manga+' '+volumename+' '+chapter[0])
			else:
				chapter_incomplete = False
				break
		if chapter_incomplete:
			summary = summary + '\nVolume '+volumename+' could not be downloaded'
			break
	if chapter_incomplete:
		continue
	postProcessImages(volumename)
	print('Compress in '+manga+' '+volumename+'.cbz')
	os.chdir(outputdir)
	shutil.make_archive('../'+manga+' '+volumename, 'zip')
	os.chdir('..')
	if not args.keep:
		shutil.rmtree(manga+' '+volumename)
	os.rename(manga+' '+volumename+'.zip', manga+' '+volumename+'.cbz')
print(summary)
