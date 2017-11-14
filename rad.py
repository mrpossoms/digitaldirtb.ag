import json
from flask import Flask
from flask import render_template

from trip import *
import posts

app = Flask('Digital Dirtbag', static_url_path='')

planner = None
posts = posts.Posts('./posts/')

@app.route("/route")
def route():
    ft_meyers = Coordinate(26.6256246, -81.9456026)
    denver = Coordinate(39.7645187, -104.9951967)
    GR = Coordinate(42.923180, -85.678650)

    if planner is None:
        planner = TripPlanner()
    stop_chain = planner.route(start=ft_meyers, destination=GR)
    return "eqfeed_callback(" + json.dumps(stop_chain) + ")"

@app.route("/")
def map():
    return render_template("main.html", posts=posts.post_markups())

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')