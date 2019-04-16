#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import sqlite3

DB_PATH = os.path.dirname(os.path.realpath(__file__)) + '/temps.db'

class NoThermometerError(Exception):
    '''
    This Error is raised if:
    - no thermometers are found, or
    - the thermometer you specified is not found
    '''
    pass

class Thermometer:
    """
    Represents a DS18B20 thermometer.
    """

    BASE_DIR = '/sys/bus/w1/devices/'
    CREATE_TEMPERATURE_TABLE = """
        CREATE TABLE IF NOT EXISTS temperature (
            timestamp DATETIME,
            temp NUMERIC);
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

    @classmethod
    def get_thermometer_ids(cls):
        ids = filter(lambda x: x.startswith('28-'), os.listdir(cls.BASE_DIR))
        return list(map(lambda x: x.lstrip('28-'), ids))

    def __init__(self, therm_id=None):
        """
        Set up a thermometer.

        Args:
        * therm_id: thermometer ID, without the '28-'
          prefix. If none is specified, choose the
          first thermometer in lexographical order.
        """
        subprocess.run(['modprobe', 'w1-gpio'], check=True)
        subprocess.run(['modprobe', 'w1-therm'], check=True)

        if therm_id is None:
            therm_ids = Thermometer.get_thermometer_ids()
            if len(therm_ids) == 0:
                raise NoThermometerError()
            else:
                self.therm_id = therm_ids[0]
        else:
            self.therm_id = therm_id

        self.device_file = '{}/28-{}/w1_slave'.format(
                self.BASE_DIR, self.therm_id)

    def get_temperature(self):
        """
        Return the current temperature in degrees Celcius.
        If thermometer is not ready, returns None. If
        thermometer is not found, raises a
        NoThermometerError.
        """
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise NoThermometerError()

        if lines[0].strip().split()[-1] != 'YES':
            return None

        return int(lines[1].strip().split('=')[1])/(10**3)

    def log_to_sqlite_db(self, db_file, time_gap=1, max_entries=10**6):
        """
        Log temperatures to an sqlite database until
        interrupted.

        Arguments:
        * db_file: sqlite database file to write to
        * time_gap: amount of time to sleep between
            thermometer reads, in seconds
        * max_entries: maximum number of entries to put
            in table --- if the table size exceeds this
            number, the oldest entries start getting
            dropped.
        """
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.executescript(self.CREATE_TEMPERATURE_TABLE.format(
            max_entries, max_entries))

        while True:
            try:
                cursor.execute("INSERT INTO temperature values("
                        "datetime('now'), {})".format(self.get_temperature()))
                conn.commit()
                time.sleep(time_gap)
            except KeyboardInterrupt:
                conn.commit()
                conn.close()
                break

def main():
    """
    A little function to test the Thermometer class. Just
    outputs a line every ~five seconds with the amount
    of time elapsed since the program started and the
    current temperature, separated by a comma.
    """
    therm = Thermometer()

    therm.log_to_sqlite_db(DB_PATH)

if __name__ == "__main__":
    main()
