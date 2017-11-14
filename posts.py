from markdown import Markdown
import os
from datetime import datetime, timezone
from flask import Markup

class Post:
    def __init__(self, path, keywords):
        self.markdown = ''
        self.html = ''
        self.date_posted = date = datetime.fromtimestamp(os.path.getctime(path), timezone.utc)
        self.keywords = keywords
        self.path = path

    def __lt__(self, other):
        return self.date_posted < other.date_posted

    def __eq__(self, other):
        return self.date_posted == other.date_posted

    def __html__(self):
        if len(self.markdown) == 0:
            with open(self.path) as post_file:
                for line in post_file:
                    self.markdown += line

        md = Markdown()
        months = [None, 'January', 'Febuary', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        date = self.date_posted
        self.html = md.convert(self.markdown) + '<center><time>%s %d, %d</time></center>' % (months[date.month], date.day, date.year)

        return self.html


class Posts:
    def __init__(self, base_path):
        self.all = []

        for path, _, names in os.walk(base_path):
            for name in names:
                if name[-3:] != '.md':
                    continue

                keywords = path.replace(base_path, '').split('/')
                keywords.pop()

                post = Post(os.path.join(path, name), keywords)

                self.all.append(post)

        self.all = sorted(self.all, reverse=True)

    def post_markups(self):
        markups = []
        for post in self.all:
            markups.append(Markup(post))

        return markups
