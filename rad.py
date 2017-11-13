import json
from flask import Flask
from flask import render_template

from trip import *
import posts

app = Flask('Digital Dirtbag')
planner = TripPlanner()
stop_chain = None

@app.route("/route")
def route():
    return "eqfeed_callback(" + json.dumps(stop_chain) + ")"

@app.route("/")
def map():
    return render_template("map.html")

if __name__ == '__main__':
    ft_meyers = Coordinate(26.6256246, -81.9456026)
    denver = Coordinate(39.7645187, -104.9951967)
    GR = Coordinate(42.923180, -85.678650)
    # stop_chain = planner.route(start=GR, destination=ft_meyers)

    posts = posts.Posts('/Users/kirk/code/digitaldirtb.ag/posts/')
    stop_chain = planner.route(start=ft_meyers, destination=GR)
    app.run(port=5000, host='0.0.0.0')