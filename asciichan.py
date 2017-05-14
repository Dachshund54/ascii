import os
import webapp2
import jinja2
import urllib2
from xml.dom import minidom

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)

IP_URL = "http://ip-api.com/xml/"

def get_coords(ip):
    ip = "4.2.2.2"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except URLError:
        return

    if content:
        d = minidom.parseString(content)
        lat_object = d.getElementsByTagName("lat")
        lon_object = d.getElementsByTagName("lon")
        if lat_object and lon_object and lat_object[0].childNodes[0].nodeValue and lon_object[0].childNodes[0].nodeValue:
            return db.GeoPt(lat_object[0].childNodes[0].nodeValue, lon_object[0].childNodes[0].nodeValue)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

class MainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery( "SELECT * FROM Art "
                            "ORDER BY created DESC "
                            "LIMIT 10")
        self.render("front.html", title=title, art=art, error=error, arts = arts)

    def get(self):
        self.write(repr(get_coords(self.request.remote_addr)))
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title = title, art = art)
            coords = get_coords(self.request.remote_addr)
            if coords:
                a.coords = coords
            a.put()

            self.redirect("/")
        else:
            error = "we need both a title and some artwork"
            self.render_front(title, art, error)

app = webapp2.WSGIApplication([ ('/', MainPage)], debug=True)
