#!/usr/bin/env python3

import RPi.GPIO as GPIO
import yaml
import time
import sys
import os
import sqlite3
from thermometer import Thermometer

CREATE_TEMPERATURE_TABLE = """
    CREATE TABLE IF NOT EXISTS temperature (
        timestamp DATETIME,
        temp NUMERIC,
        proportional NUMERIC,
        integral NUMERIC,
        derivative NUMERIC,
        duty_cycle NUMERIC);
    DROP TRIGGER IF EXISTS rowcount;
    CREATE TRIGGER IF NOT EXISTS rowcount
    BEFORE INSERT ON temperature
    WHEN (SELECT COUNT(*) FROM temperature) >= {}
    BEGIN
        DELETE FROM temperature WHERE timestamp NOT IN (
            SELECT timestamp FROM temperature
            ORDER BY timestamp DESC
            LIMIT {}
        );
    END
"""

def basic_thermostat(relay_pin, thermometer, set_point, delay_time,
        db_connection, db_cursor):
    """
    Implements a basic thermostat --- if the current
    temperature is below the set point, it turns the boiler
    on; if the temperature is above the set point, it turns
    the boiler off.

    Arguments:
    * relay_pin: GPIO pin controlling the relay, in BCM
        numbering
    * thermometer: a Thermometer instance
    * set_point: the temperature to aim for, in deg C
    * delay_time: time between readings, in seconds
    """
    pwm = GPIO.PWM(relay_pin, 1)
    pwm.start(0)
    while True:
        temp = thermometer.get_temperature()
        if temp < set_point:
            output = 70
        else:
            output = 0
        pwm.ChangeDutyCycle(output)
        # log the temperature, P/I/D terms, and output
        db_cursor.execute("INSERT INTO temperature values(datetime('now'),"
                "{}, {}, {}, {}, {})".format(
                    temp, set_point - temp, 0, 0, output))
        db_connection.commit()
        time.sleep(delay_time)

def pid(relay_pin, thermometer, set_point, K_p, K_i, K_d, db_connection,
        db_cursor, max_integral, max_error_accumulation=5,
        delay_time=1, frequency=1):
    """
    Implements a proportional-integral-derivative
    controller, which intelligently modifies the
    pulse width of the boiler to keep the temperature
    from swinging too much.

    Arguments:
    * relay_pin: the GPIO pin controlling the relay, in
        BCM numbering
    * thermometer: a Thermometer instance
    * set_point: the temperature to aim for, in deg C
    * K_p, K_i, K_d: the PID controller constants for the
        proportional, integral, and derivative terms,
        respectively.
    * db_connection: sqlite3 Connection
    * db_cursor: sqlite3 Cursor
    * max_integral: maximum value integral term is allowed
      to reach, to prevent integral windup
    * max_error_accumulation: maximum abs(error), in
      degrees C, under which integral term is allowed to
      accumulate
    * delay_time: time between readings, in seconds
    * frequency: frequency of PWM, in Hz
    """

    pwm = GPIO.PWM(relay_pin, frequency)
    pwm.start(0)

    previous_integral = 0.0
    previous_error = 0
    previous_time = time.time()
    while True:
        current_temperature = thermometer.get_temperature()
        current_time = time.time()

        # calculate the proportional, integral, and derivative terms
        error = set_point - current_temperature
        delta_t = current_time - previous_time
        derivative = (error - previous_error) / delta_t

        integral = previous_integral + 0.5 * (error + previous_error) * delta_t
        if integral > max_integral:
            integral = 0
        if abs(error) > max_error_accumulation:
            integral = previous_integral
        if current_temperature < 80:
            integral = 0

        # calculate the output and set boiler
        new_duty_cycle = K_p * error + K_i * integral + K_p * derivative
        # confine duty cycle in range [0,100]
        new_duty_cycle = max(0, min(new_duty_cycle, 100))
        pwm.ChangeDutyCycle(new_duty_cycle)

        # log the temperature, P/I/D terms, and output
        db_cursor.execute("INSERT INTO temperature values(datetime('now'),"
                "{}, {}, {}, {}, {})".format(thermometer.get_temperature(),
                    error, integral, derivative, new_duty_cycle))
        db_connection.commit()

        # keep track of current terms for next cycle through loop
        previous_integral = integral
        previous_error = error
        previous_time = current_time

        time.sleep(delay_time)

def main():
    # load configuration file
    config = yaml.safe_load(open(sys.argv[1], 'r'))

    # set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config['relay_pin'], GPIO.OUT)

    # set up database
    connection = sqlite3.connect(config['db_path'])
    cursor = connection.cursor()
    cursor.executescript(CREATE_TEMPERATURE_TABLE.format(
        config['max_entries'], config['max_entries']))

    # set up thermometer
    thermometer = Thermometer()

    try:
#        basic_thermostat(config['relay_pin'], thermometer, config['set_point'],
#            1, connection, cursor)
        pid(config['relay_pin'], thermometer, config['set_point'],
                config['K_p'], config['K_i'], config['K_d'], connection, cursor,
                config['max_i'], config['max_error_accumulation'],
                config['delay_time'])
    except KeyboardInterrupt:
        connection.commit()
        connection.close()

if __name__ == '__main__':
    try: main()
    except Exception as e: print(e, file=sys.stderr)
    finally: GPIO.cleanup()
