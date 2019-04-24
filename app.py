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
CONFIG_FILE = '/home/pi/piggia/config.yaml'

class PlotForm(FlaskForm):
    plot_interval = DecimalField('Time to plot (hours)')
    submit = SubmitField('Replot')

def convert_to_local_time(date_time):
    return date_time.replace(tzinfo=dt.timezone.utc).astimezone(tz=None)

@app.route('/', methods=['GET', 'POST'])
def index():
    config = yaml.safe_load(open(CONFIG_FILE, 'r'))

    conn = sqlite3.connect(config['db_path'])
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM temperature ORDER BY timestamp DESC LIMIT 1")
    time, temp = cursor.fetchall()[0][:2]
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

def make_plot(times, temps, errors, integrals, derivatives, outputs, config):
    img = io.BytesIO()

    fig, axs = plt.subplots(5, 1, sharex=False, figsize=(8, 30))

    #plt.xticks(rotation=90)
    axs[0].plot(times, temps)
    axs[0].axhline(y=90, color='grey', linestyle=':')
    axs[0].axhline(y=config['set_point'], color='grey', linestyle=':')
    axs[0].axhline(y=96, color='grey', linestyle=':')
    axs[0].set_ylabel('Temperature (deg C)')
    axs[0].grid()

    axs[1].plot(times, errors)
    axs[1].axhline(y=0, color='grey', linestyle=':')
    axs[1].set_ylabel('Error (deg C)')
    axs[1].grid()

    axs[2].plot(times, integrals)
    axs[2].axhline(y=0, color='grey', linestyle=':')
    axs[2].set_ylabel('Integral(Error dt)')
    axs[2].grid()

    axs[3].plot(times, derivatives)
    axs[3].axhline(y=0, color='grey', linestyle=':')
    axs[3].set_ylabel('dE/dt')
    axs[3].grid()

    axs[4].plot(times, outputs)
    axs[4].set_ylabel('Boiler output (%)')
    axs[4].grid()

    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()

    return img

@app.route('/temps.png')
def temps_png():
    # load configuration file
    config = yaml.safe_load(open(CONFIG_FILE, 'r'))

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
    errors = list(map(lambda p: float(p[2]), pairs))
    integrals = list(map(lambda p: float(p[3]), pairs))
    derivatives = list(map(lambda p: float(p[4]), pairs))
    outputs = list(map(lambda p: float(p[5]), pairs))

    img = make_plot(times, temps, errors, integrals, derivatives,
            outputs, config)

    return Response(img.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
