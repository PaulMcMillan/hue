from time import sleep

import pytest

from hue import Hue

# Modify the class slightly before using it to avoid ambiguous data
Hue.devicetype = 'PythonHueClientTests'

@pytest.fixture(scope="module")
def testhue(request):
    return Hue.discover_one('BasePythonHueClientTestUser')


@pytest.fixture(autouse=True)
def cleanup_link_button(testhue):
    # Always set this back to a safe state at the end of a test function
    testhue.deactivate_link_button()


def test_arg_devicetype():
    myhue = Hue.discover_one()
    assert myhue.devicetype == 'PythonHueClientTests'
    myhue = Hue.discover_one(devicetype='PythonHueTestClient2')
    assert myhue.devicetype == 'PythonHueTestClient2'


def test_get_config(testhue):
    conf = testhue.get_config()
    assert testhue.username in conf['whitelist']


def test_get_config_non_whitelist(testhue):
    unwhitelisted_name = 'woogyboogy_nowhitelist'
    assert unwhitelisted_name not in testhue.get_config()['whitelist']
    myhue = Hue.discover_one(unwhitelisted_name)
    conf = myhue.get_config()
    # We only get a minimal config when not whitelisted
    assert conf.keys() == ['swversion', 'name']


def test_get_full_state(testhue):
    full_state= testhue.get_full_state()
    assert testhue.username in full_state['config']['whitelist']


def test_activate(testhue):
    testhue.activate_link_button()
    conf = testhue.get_config()
    assert conf['linkbutton'] == True
    testhue.deactivate_link_button()
    conf = testhue.get_config()
    assert conf['linkbutton'] == False
    with pytest.raises(Exception):
        testhue.create_user('ShouldNotExist')
    testhue.activate_link_button()
    conf = testhue.get_config()
    assert conf['linkbutton'] == True


def test_autocreate_user(testhue):
    testhue.activate_link_button()
    # Let the device create a user
    myhue = Hue.discover_one(devicetype='PythonHueClientTests')
    assert len(myhue.create_user()) > 10
    assert myhue.devicetype == 'PythonHueClientTests'
    conf = myhue.get_config()
    # we got the full config values
    assert 'whitelist' in conf
    myhue.delete_user()
    # And now this user is no longer whitelisted
    with pytest.raises(Exception):
        myhue.deactivate_link_button()


def test_user_length():
    with pytest.raises(Exception):
        myhue = Hue.discover_one('tooshort', 'PythonHueClientTests')


def test_create_user(testhue):
    testhue.activate_link_button()
    myhue = Hue.discover_one('PythonHueClientTest', 'PythonHueClientTests')
    myhue.create_user()
    conf = myhue.get_config()
    # we got the full config values
    assert 'whitelist' in conf
    myhue.delete_user()
    with pytest.raises(Exception):
        # Our user is invalid, so we can't do this
        myhue.deactivate_link_button()


def test_create_another_user(testhue):
    testhue.activate_link_button()
    testhue.get_config()
    assert 'TestOtherUser' not in testhue.config['whitelist']
    testhue.create_user('TestOtherUser')
    testhue.get_config()
    assert 'TestOtherUser' in testhue.config['whitelist']
    testhue.delete_user('TestOtherUser')
    testhue.get_config()
    assert 'TestOtherUser' not in testhue.config['whitelist']


def test_modify_config(testhue):
    old_config = testhue.get_config()
    testhue.modify_config(name='TempTestName')
    testhue.get_config()
    assert testhue.config['name'] == 'TempTestName'
    testhue.modify_config(name=old_config['name'])
    new_config = testhue.get_config()
    assert new_config['name'] == old_config['name']


def test_get_lights(testhue):
    #XXX actually test this
    print testhue.get_lights()


def test_get_new_lights(testhue):
    #XXX actually test this
    print testhue.get_new_lights()


# Disabled till we figure out the impact of running this a bunch
def test_search_new_lights(testhue):
    """ Scan for new lights """
    #print testhue.search_new_lights()


def test_base_lights(testhue):
    lights = testhue.get_lights()
    for light in lights:
        assert light
        assert hasattr(light, 'bridge')
        assert hasattr(light, 'light_id')
        assert hasattr(light, 'name')


@pytest.fixture(scope="module")
def lights(testhue):
    lights = testhue.get_lights()
    for light in lights:
        light.get()
    return lights

def test_light_extended_attributes(lights):
    for light in lights:
        assert hasattr(light, 'state')
        assert hasattr(light, 'swversion')
        assert hasattr(light, 'type')

def test_light_state(lights):
    for light in lights:
        pass

def test_put_state(lights):
    # Sleeps in here for now since going too fast breaks it
    for light in lights:
        light.put_state(bri=1)
        sleep(.1)
        light.get()
        assert light.state['bri'] == 1
        light.put_state(bri=100)
        sleep(.1)
        light.get()
        assert light.state['bri'] == 100
