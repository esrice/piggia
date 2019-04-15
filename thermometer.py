#!/usr/bin/env python3

import subprocess

class Thermometer:
    def __init__(self, therm_id=None):
        subprocess.run(['modprobe', 'w1-gpio'], check=True)
        subprocess.run(['modprobe', 'w1-therm'], check=True)

        if not therm_id:
            pass # TODO find the thermometer id

        self.device_file = '/sys/bus/w1/devices/28-{}/w1_slave'.format(therm_id)

    def get_temperature():
        with open(self.device_file, 'r') as f:
            lines = f.readlines()

        if lines[0].strip().split()[-1] != 'YES':
            raise NoTempError()
