from hue import Hue

new_hue = Hue.discover_one('BasePythonHueClientTestUser',
                           'PythonHueClientTests')
try:
    result = new_hue.create_user()
except Exception:
    raw_input('Press the link button now, then press enter.')
    result = new_hue.create_user()
print "User %s successfully added. Tests should run now." % result
