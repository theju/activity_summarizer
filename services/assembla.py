from jinja2 import Template
import requests
import xml.etree.ElementTree as ET
import datetime

class Assembla(object):
    def __init__(self, username=None, password=None, url_template=None, settings=None):
        self.username = username
        self.password = password
        self.url_template = Template(url_template)
        self.assembla_user_url = Template("https://www.assembla.com/user/best_profile/")
        self.settings = settings or {}

    def render(self):
        stream = []
        url = self.url_template.render()
        resp = requests.get(self.assembla_user_url.render(),
                            auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                            headers={'Accept': 'application/xml', 'Content-Type': 'application/xml'})
        if not resp.text.strip():
            return stream
        root = ET.fromstring(resp.text)
        user_id = root.find("id").text
        resp = requests.get(url, auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                            headers={'Accept': 'application/xml', 'Content-Type': 'application/xml'})
        if resp.status_code != 200:
            return stream

        from_date = datetime.date.today()
        if self.settings.get("from_date"):
            from_date = datetime.datetime.strptime(self.settings["from_date"], "%Y-%m-%dT%H:%M:%SZ")

        to_date = from_date + datetime.timedelta(days=1)
        if self.settings.get("to_date"):
            to_date = datetime.datetime.strptime(self.settings["to_date"], "%Y-%m-%dT%H:%M:%SZ")

        root = ET.fromstring(resp.text)
        for event in root.findall("event"):
            if event.find("author").find("id").text != user_id:
                continue
            # TODO: Remove the hardcoding of the timezone
            created_date = datetime.datetime.strptime(event.find("date").text, "%a %b %d %H:%M:%S +0000 %Y").date()
            if created_date > to_date:
                continue
            if created_date < from_date:
                continue
            description = "* %s %s" % (event.find("operation").text, event.find("title").text)
            stream.append((created_date, description))
        return stream
