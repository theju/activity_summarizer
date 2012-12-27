import requests
import json
import datetime
from jinja2 import Template

class Github(object):
    def __init__(self, username=None, token=None, url_template=None, settings=None):
        self.username = username
        self.token = token
        self.url_template = Template(url_template)
        self._event_type_templates = {
            "CommitCommentEvent": Template("* Posted comment (#{{comment.id}}) on {{comment.url}}: {{comment.body}}"),
            "CreateEvent": Template("* Created {{ref_type}}: {{description}}"),
            "ForkEvent": Template("* Forked {{forkee.name}}"),
            "IssueCommentEvent": Template("* Commented on (#{{issue.number}}): {{issue.body}}"),
            "IssuesEvent": Template("* {{action}} issue {{issue.number}} with {{issue.body}}"),
            "PullRequestEvent": Template("* {{action}} Pull Request (#{{number}}): {{pull_request.body}}"),
            "PullRequestReviewCommentEvent": Template("* Commented on pull request: {{comment.body}}"),
            "PushEvent": Template("{% for commit in commits %}* {{ commit.message }}\n{% endfor %}")
            }
        self.settings = settings or {}

    def _render_event(self, event):
        event_type = event["type"]
        if not event_type:
            return None
        event_template = self._event_type_templates[event_type]
        return event_template.render(**event["payload"])

    def render(self):
        stream = []
        url = self.url_template.render(**{"username": self.username,
                                          "token": self.token})
        resp = requests.get(url)
        if resp.status_code != 200:
            return stream

        from_date = datetime.date.today()
        if self.settings.get("from_date"):
            from_date = datetime.datetime.strptime(self.settings["from_date"], "%Y-%m-%dT%H:%M:%SZ")

        to_date = from_date + datetime.timedelta(days=1)
        if self.settings.get("to_date"):
            to_date = datetime.datetime.strptime(self.settings["to_date"], "%Y-%m-%dT%H:%M:%SZ")

        for event in resp.json:
            created_date = datetime.datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
            if created_date > to_date:
                continue
            if created_date < from_date:
                continue
            description = self._render_event(event)
            if description:
                stream.append((created_date, description))
        return stream
