#!/usr/bin/env python3

from flask import Flask, Response, render_template, request
from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField

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
app.secret_key = 'development key'
SQL_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class PlotForm(FlaskForm):
    plot_interval = DecimalField('Time to plot (hours)')
    submit = SubmitField('Replot')

def convert_to_local_time(date_time):
    return date_time.replace(tzinfo=dt.timezone.utc).astimezone(tz=None)

@app.route('/', methods=['GET', 'POST'])
def index():
    config = yaml.safe_load(open(sys.argv[1], 'r'))

    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM temperature ORDER BY timestamp DESC LIMIT 1")
    time, temp = cursor.fetchall()[0]
    conn.close()

    time = convert_to_local_time(dt.datetime.strptime(time, SQL_TIME_FORMAT))

    form = PlotForm()

    if request.method == 'POST':
        plot_interval = request.form['plot_interval']
    else:
        plot_interval = config['plot_interval']
    plot = 'temps.png?plot_interval={}'.format(plot_interval)

    return render_template('index.html', temp=temp, time=time, form=form,
            plot=plot)

@app.route('/temps.png')
def temps_png():
    # load configuration file
    config = yaml.safe_load(open(sys.argv[1], 'r'))

    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()

    plot_interval = request.args.get('plot_interval') or config['plot_interval']
    cursor.execute("SELECT * FROM temperature "
            "WHERE timestamp > datetime('now', '-{} hours')".format(
                plot_interval))
    pairs = cursor.fetchall()

    time_lambda = lambda p: dt.datetime.strptime(p[0], SQL_TIME_FORMAT)
    times = list(map(convert_to_local_time, map(time_lambda, pairs)))
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
