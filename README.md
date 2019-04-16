# piggia
Controlling a Gaggia with a Raspberry Pi

## Introduction
This is very simple software for using a Raspberry Pi with a Gaggia Classic
espresso machine. Right now, it just logs temperature and displays it on a
webpage. Eventually, it will function as a PID controller for the boiler too.

## Hardware
To measure the boiler temperature, I use a DS18B20 thermometer wired in the
standard (not phantom power) way. I will upload an actual circuit diagram soon,
but in the meantime, see Figure 7 of the
[datasheet](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf).

You'll also need to enable the thermometer by adding the following line to
`/boot/config.txt`:
```
dtoverlay=w1-gpio,gpiopin=4
```
You can change `gpiopin` to whatever pin you actually want to use. Be sure to
specify the pin with the broadcom numbering scheme.

## Installation
First, install the requirements:
```
sudo apt-get install sqlite3 python3-matplotlib python3-pip git
pip3 install Flask
```

Then, download the code:
```
git clone https://github.com/esrice/piggia.git
```

Finally, add the following lines to `/etc/rc.local` to make the temperature
logger and web server start running automatically when the Raspberry Pi starts
up:
```
sudo python3 /path/to/thermometer.py &
sudo python3 /path/to/app.py &
```
You can run these in a terminal too, of course. You should now have a little
webpage showing the current temperature and a plot of past temperatures at
`http://raspberrypi.local:5000`.
