from random import randint
from time import sleep

from hue import Hue

myhue = Hue.discover_one('ExampleScript')

lights = myhue.get_lights()
for light in lights:
    light.put_state(on=True)

try:
    while True:
        for light in lights:
            sleep(.1)
            light.put_state(hue=randint(0, 65535),
                            bri=randint(0, 100))
except KeyboardInterrupt:
    for light in lights:
        light.put_state(on=False)
