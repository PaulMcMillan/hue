from pprint import pprint
import json

import requests

class BaseHue(object):
    """ Base methods for the Hue class. """
    @classmethod
    def discover(cls, username='', devicetype=None):
        """ Discover the local (private) ip for hue bridges on your network.

        Returns a list of Hue objects on your local network for
        further interaction.
        """
        # XXX need to work on this. Discovering a gateway shouldn't
        # require specifying a user, but the only common case after
        # this is to do user-stuff (and end up with a confusing error)
        res = requests.get('http://www.meethue.com/api/nupnp').json()
        return [cls(username=username, devicetype=devicetype, **hue)
                for hue in res]

    @classmethod
    def discover_one(cls, *args, **kwargs):
        return cls.discover(*args, **kwargs).pop()

    def _make_request(self, method, url_path, data=None,
                     prepend_auth=True):
        # Not entirely comfortable with putting this in the base, but
        # it'll do for now.
        if prepend_auth:
            if not self.username:
                raise Exception('No username specified. Username is required '
                                'for uris that require whitelisting.')
            url_path = '/api/' + self.username + url_path
        url = 'http://%s' % self.internalipaddress + url_path
        if data:
            res = requests.request(
                method=method, url=url, data=json.dumps(data)).json()
        else:
            res = requests.request(
                method=method, url=url).json()
        # XXX DEBUG
        print method, url, data
        print 'Result: ',
        pprint(res)

        if not isinstance(res, list):
            # Non-error GETs usually return dictionaries. We don't
            # have explicit promise about this in the API though.
            return res
        # Raise an exception for any errors. We're only going to raise
        # the first one, but the API promises it's the most
        # relevant. There's not a more absolute way to detect an error
        # than "dictionary in a list with an 'error' key". Hopefully
        # the API won't start returning lists that contain things in
        # another form.
        for r in res:
            if 'error' in r:
                # I'm not sure how I feel about this, but hue is
                # returning success and errors mixed together, so this
                # seems like the most reasonable way to allow an error
                # handler to recover smoothly
                e = Exception(r['error'])
                e.result = res
                raise e
        return [r['success'] for r in res if 'success' in r]

    def get(self, *args, **kwargs):
        return self._make_request('GET', *args, **kwargs)
    def post(self, *args, **kwargs):
        return self._make_request('POST', *args, **kwargs)
    def put(self, *args, **kwargs):
        return self._make_request('PUT', *args, **kwargs)
    def delete(self, *args, **kwargs):
        return self._make_request('DELETE', *args, **kwargs)


class Hue(BaseHue):
    """ A representation of a hue bridge.
    """

    devicetype = 'PythonHueClient'

    def __init__(self, internalipaddress, username, devicetype=None,
                 macaddress=None, id=None, **kwargs):
        """ Create a new Hue instance.

        :param internalipaddress: Internal IP address for the hue bridge

        :param username: A username. If this is not provided, a random
        key will be generated and returned in the response. It is
        recommended that a unique identifier for the device be used as
        the username
        :type username: string 10..40

        :param devicetype: Description of the type of device
        associated with this username.

        :type devicetype: string 0..40

        """
        if devicetype:
            self.devicetype = devicetype
        if username and not (40 >= len(username) >= 10):
            # XXX: better exceptions
            raise Exception('Username not between 10 and 40 characters.')
        self.username = username
        self.internalipaddress = internalipaddress
        self.macaddress = macaddress
        self.identity = id

    def create_user(self, username=None):
        """ Create a new user on the bridge. Press the link button, then
        run this command within 30 seconds.

        Please use a unique and descriptive application name.
        """
        data = {'devicetype': self.devicetype}

        # Prefer the provided username
        if username:
            data['username'] = username
        # But use the username from this object if not provided
        elif self.username:
            data['username'] = self.username
        # If this object doesn't have a username, the bridge will
        # generate one.

        res = self.post('/api', data, prepend_auth=False).pop()
        # Handle the case where the bridge assigns us a username
        if not username:
            self.username = res['username']
        return res['username']

    def delete_user(self, username=None):
        """ Removes a specified user (or the current hue user if no
        user given) from the whitelist.
        """
        if not username:
            username = self.username
        res = self.delete('/config/whitelist/' + username)

    def activate_link_button(self):
        """ If your user is already whitelisted, this is equivalent to
        pressing the link button.

        Obviously it doesn't work if you don't have a whitelisted user.
        """
        return self.put('/config', {'linkbutton': True})

    def get_config(self):
        res = self.get('/config')
        self.config = res
        return res

    def modify_config(self, **kwargs):
        return self.put('/config', data=kwargs)

    def deactivate_link_button(self):
        """ Unpresses the link button. """
        return self.modify_config(linkbutton=False)

    def get_full_state(self):
        """ Returns the entire device state. Expensive operation, use
        it sparingly.
        """
        return self.get('')

    def get_lights(self):
        """ Gets a list of all lights that have been discovered. """
        res = self.get('/lights')
        # maybe not a list here?
        return [HueLight(self, light_id, data) for
                light_id, data in res.items()]

    def get_new_lights(self):
        """ Gets a list of lights discovered since the last search. """
        res = self.get('/lights/new')
        return res
        # XXX lastscan + a list of new lights... how to return this nicely

    def search_new_lights(self):
        """ Start a search for new lights. """
        return self.post('/lights')


class HueLight(object):
    def __init__(self, bridge, light_id, data):
        self.bridge = bridge
        self.light_id = light_id
        for k, v in data.items(): #usually just "name"
            setattr(self, k, v)
        self.path_fragment = '/lights/' + self.light_id

    def get(self):
        """ Get attributes and state of light """
        res = self.bridge.get(self.path_fragment)
        for k, v in res.items():
            setattr(self, k, v)
        return res

    def rename(self, name):
        """ Rename the light """
        return self.bridge.put(self.path_fragment, data={'name': name})

    def put_state(self, **kwargs):
        # Handle error 201 (light off)
        return self.bridge.put(self.path_fragment + '/state', data=kwargs)
