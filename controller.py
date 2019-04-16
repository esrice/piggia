#!/usr/bin/env python3

import RPi.GPIO as GPIO
import yaml
import time
import sys
import os
from thermometer import Thermometer

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

def basic_thermostat(relay_pin, thermometer, set_point, delay_time):
    while True:
        temp = thermometer.get_temperature()
        if temp < set_point:
            GPIO.output(relay_pin, GPIO.HIGH)
        else:
            GPIO.output(relay_pin, GPIO.LOW)
        time.sleep(delay_time)

def main():
    # load configuration file
    config = yaml.safe_load(open(sys.argv[1], 'r'))

    # set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config['relay_pin'], GPIO.OUT)

    thermometer = Thermometer()

    try:
        basic_thermostat(config['relay_pin'], thermometer, config['set_point'],
                config['delay_time'])
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == '__main__':
    try: main()
    except Exception as e: print(e, file=sys.stderr)
    finally: GPIO.cleanup()
