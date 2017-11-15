import json
from flask import Flask
from flask import render_template

from trip import *
from posts import Posts

app = Flask('Digital Dirtbag', static_url_path='')


@app.route("/route")
def route():
    ft_meyers = Coordinate(26.6256246, -81.9456026)
    denver = Coordinate(39.7645187, -104.9951967)
    GR = Coordinate(42.923180, -85.678650)

    planner = TripPlanner()
    stop_chain = planner.route(start=ft_meyers, destination=GR)
    return "eqfeed_callback(" + json.dumps(stop_chain) + ")"


@app.route("/")
@app.route("/posts")
def index():
    posts = Posts('./posts/')
    return render_template("main.html", start=0, end=5, posts=posts)


@app.route("/posts/<int:start>/<int:end>")
def post_select(start, end):
    posts = Posts('./posts/')
    return render_template("main.html", start=start, end=end, posts=posts)


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
