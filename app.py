#!/usr/bin/env python3

from flask import Flask, Response, render_template
import sqlite3
import io
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime as dt
import sys
import yaml

app = Flask(__name__)
SQL_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DB_PATH = os.path.dirname(os.path.realpath(__file__)) + '/temps.db'

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM temperature ORDER BY timestamp DESC LIMIT 1")
    time, temp = cursor.fetchall()[0]
    conn.close()

    return render_template('index.html', temp=temp, time=time)

@app.route('/temps.png')
def temps_png():
    # load configuration file
    config = yaml.safe_load(open(sys.argv[1], 'r'))

    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM temperature "
            "WHERE timestamp > datetime('now', '-{} hours')".format(
                config['plot_interval']))
    pairs = cursor.fetchall()

    time_lambda = lambda p: dt.datetime.strptime(p[0], SQL_TIME_FORMAT)
    tz_lambda = lambda t: t.replace(tzinfo=dt.timezone.utc).astimezone(tz=None)
    times = list(map(tz_lambda, map(time_lambda, pairs)))
    temps = list(map(lambda p: float(p[1]), pairs))

    img = io.BytesIO()
    plt.xticks(rotation=90)
    plt.plot(times, temps)
    plt.xlabel('Time')
    plt.ylabel('Temperature (deg C)')
    plt.axhline(y=90, color='grey', linestyle=':')
    plt.axhline(y=93, color='grey', linestyle=':')
    plt.axhline(y=96, color='grey', linestyle=':')
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return Response(img.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
