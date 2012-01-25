import wsgiref.handlers
import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, None))

apps_binding = []
apps_binding.append(('/', MainPage))
application = webapp.WSGIApplication(apps_binding, debug=False)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()