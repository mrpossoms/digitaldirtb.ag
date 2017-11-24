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
    stop_set = planner.route(start=GR, destination=denver)
    nearby, nearby_dics, stop_dics = [], [], []

    for stop in stop_set:
        surrounding = planner.trails.trails(stop, within=1);
        stop_dics.append(stop.as_dictionary)

        for near in surrounding:
            if near in nearby or near in stop_set:
                continue

            nearby.append(near)
            nearby_dics.append(near.as_dictionary)

    trails = {'route': stop_dics, 'other': nearby_dics}

    return "eqfeed_callback(" + json.dumps(trails) + ")"

@app.route("/map")
def map():
    return render_template('map.html')


@app.route("/")
@app.route("/posts")
def index():
    posts = Posts('./posts/')
    return render_template("posts.html", start=0, end=5, posts=posts)


@app.route("/posts/<int:start>/<int:end>")
def post_select(start, end):
    posts = Posts('./posts/')
    return render_template("posts.html", start=start, end=end, posts=posts)


if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
