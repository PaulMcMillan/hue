#!/usr/bin/python
from random import randint
from time import sleep

from hue import Hue

myhue = Hue.discover_one('ExampleScript')

lights = myhue.get_lights()
for light in lights:
    light.put_state(on=True, transitiontime=10)

try:
    interval = 5
    while True:
        for light in lights:
            light.put_state(hue=randint(0, 65535),
                            sat=randint(200, 255),
                            bri=randint(200, 255),
                            # Transition is an integer in steps of 100ms
                            transitiontime=int(interval * 10))
            sleep(interval/len(lights))

except KeyboardInterrupt:
    for light in lights:
        light.put_state(on=False, transitiontime=10)
