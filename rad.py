import json
from flask import Flask
from flask import render_template

from trip import TripPlanner


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
    stop_chain = planner.route()
    app.run(host='0.0.0.0')
