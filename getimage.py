#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# IMG2JSON
# 
# Extract meta data from an image url

import wsgiref.handlers
import os
import logging
import StringIO
import struct
import exif

from google.appengine.ext import webapp
from google.appengine.api import images
from google.appengine.api.urlfetch import *
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class GetImage(webapp.RequestHandler):

  def get(self):
	self.response.headers['Content-Type'] = 'application/json'
	
	# Get the querystring params
	image_url = self.request.get("url", None)
	callback = self.request.get("callback", None)
	
	logging.debug("Fetching %s", image_url)
	
	# Download the image from the passed URL param in QS
	response = fetch(image_url)
	
	if self.isValidFileExtension(image_url) == False:
		logging.error("Invalid image extension: %s", image_url)
		self.response.out.write("{ error: 'Image does not look valid based on its filename: " + image_url + "' }")
		return
	
	# If there was a problem fetching the URL grab the default logo
	if response.status_code != 200:
		logging.error("Error fetching image %s", image_url)
		self.response.out.write("{ error: 'Error fetching image: " + image_url + "'}")
		return
	
	image_content = response.content
	image_info = self.getImageInfo(image_content)
	image_content_type = image_info[0]
	image_width = image_info[1]
	image_height = image_info[2]
	image_byte_size = image_info[3]
	image_exif_tags = exif.parse( StringIO.StringIO(image_content), 255, mode=exif.ASCII )

	template_values = {
		'url': image_url,
		'mime_type': image_content_type,
		'width': image_width,
		'height': image_height,
		'byte_size': image_byte_size,
		'callback': callback,
		'exif': image_exif_tags
	}

	path = os.path.join(os.path.dirname(__file__), 'response.json')
	self.response.out.write(template.render(path, template_values))


  def isValidFileExtension(a,image_url):
	extList = ["jpg", "jpeg", "png", "gif", "bmp"]
	try:
		split_url = image_url.split(".")
		if split_url[len(split_url)-1] in extList: return True
		else: return False
	except:
		return False


  def getImageInfo(first,data):
	data = str(data)
	size = len(data)
	height = -1
	width = -1
	content_type = ''

	# handle GIFs
	if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
		# Check to see if content_type is correct
		content_type = 'image/gif'
		w, h = struct.unpack("<HH", data[6:10])
		width = int(w)
		height = int(h)

	# See PNG v1.2 spec (http://www.cdrom.com/pub/png/spec/)
	# Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
	# and finally the 4-byte width, height
	elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n') and (data[12:16] == 'IHDR')):
		content_type = 'image/png'
		w, h = struct.unpack(">LL", data[16:24])
		width = int(w)
		height = int(h)

	# Maybe this is for an older PNG version.
	elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
		# Check to see if we have the right content type
		content_type = 'image/png'
		w, h = struct.unpack(">LL", data[8:16])
		width = int(w)
		height = int(h)

	# handle JPEGs
	elif (size >= 2) and data.startswith('\377\330'):
		content_type = 'image/jpeg'
		jpeg = StringIO.StringIO(data)
		jpeg.read(2)
		b = jpeg.read(1)
		try:
			while (b and ord(b) != 0xDA):
				while (ord(b) != 0xFF): b = jpeg.read(1)
				while (ord(b) == 0xFF): b = jpeg.read(1)
				if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
					jpeg.read(3)
					h, w = struct.unpack(">HH", jpeg.read(4))
					break
				else:
					jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
					b = jpeg.read(1)
			width = int(w)
			height = int(h)
		except struct.error:
			pass
		except ValueError:
			pass

	return content_type, width, height, size



apps_binding = []
apps_binding.append(('/go/', GetImage))
application = webapp.WSGIApplication(apps_binding, debug=False)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()