#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import urllib
import ConfigParser
import options

BASE_URL = "https://www.fullsms.de/gw/"


USER     = 'user'
PASSWORD = 'password'
GATEWAY  = 'gateway'
RECEIVER = 'receiver'
SENDER   = 'sender'
SETTINGS = [USER, PASSWORD, GATEWAY, RECEIVER, SENDER]

GATEWAYS = dict(('_'+str(g), g) for g in [11, 26, 31, 12, 22, 27, 32])
for key, value in GATEWAYS.items():
    globals()[key] = value

DEFAULTS = dict((zip(SETTINGS, [None] *len(SETTINGS))))
DEFAULTS[GATEWAY] = _22

DEBUG = False

SEND = 'send'
CHECK = 'check'
SUBS = [SEND, CHECK]
optspec = """
sms %s [-d] <message...>
--
 general program options
d,debug     activate debugging
h,help      display help and exit
 for all subcommands
u,user=     the fullsms.de username
p,password= the fullsms.de password
 for 'send' only
g,gateway=  the gateway to use
r,receiver= the person to send the message to
s,sender=   the sender to use
""" % ('[' + ' | '.join(SUBS) + ']')
parser = options.Options(optspec)

def warn(message):
    print "Warning: %s" % message

def fatal(message):
    parser.fatal(message)

def debug(message):
    if DEBUG:
        print "Debug: %s" % message


def parse_config(section='settings', config_filename="~/.fullsms"):
    """ Parse a configuration file with app settings.

    Parameters
    ----------
    section : str
        the name of the config section where to look for settings
        (default: 'settings')
    config_filename : str
        the path to and name of the config file
        (default: '~/.fullsms')

    Returns
    -------
    settings : dict
        any settings found in the config file

    Raises
    ------
    IOError:
        if config_filename does not exist
    NoSectionError
        if no section with name 'section' exists

    """
    config_filename = os.path.expanduser(config_filename)
    cp = ConfigParser.RawConfigParser()
    with open(config_filename) as fp:
        cp.readfp(fp)
    sets = dict(cp.items(section))
    for key in sets.keys():
        if key not in SETTINGS:
            warn("Setting %s not recognized!")
    return sets

def assemble_rest_call(function, parameters):
    """ Create a URL suitable for making a REST call to fullsms.de

    Parameters
    ----------
    function : str
        the api function to execute
    parameters : dict
        the parameters to use in the call

    Returns
    -------
    url : str
        an ready made url

    """
    query = urllib.urlencode(sorted(parameters.items()))
    return "%s%s?%s" % (BASE_URL, function, query)

def call(str_):
    file_like = urllib.urlopen(str_)
    return file_like.read()

def assemble_send_str(params):
    return assemble_rest_call('', params)

def assemble_check_str(params):
    return assemble_rest_call('konto.php', params)

def send(user, password, gateway, receiver, sender, message):
    parameters = {
            'user': user,
            'passwort': password,
            'typ': gateway,
            'handynr': receiver,
            'absender': sender,
            'text': message
            }
    rest_str = assemble_rest_call('', parameters)
    return call(rest_str)

def check(user, password):
    params = {'user': user, 'passwort': password}
    str_ = assemble_check_str(params)
    return call(str_)

def set_setting(setting, conf, cli):
    order = [('default',
                lambda x: DEFAULTS[x] is not None,
                lambda x: DEFAULTS[x]),
             ('conf file',
                lambda x: conf.has_key(x),
                lambda x: conf[x]),
             ('command line',
                lambda x: cli[x] is not None,
                lambda x: cli[x])
            ]
    prev, val = None, None
    for desc, has, get in order:
        if has(setting):
            if val is not None:
                val = get(setting)
                debug("Value for '%s' found on %s, overrides %s: '%s'"
                        % (setting, desc, prev, val))
            else:
                val = get(setting)
                debug("Value for '%s' found in %s: '%s'"
                        % (setting, desc, val))
        prev = desc
    if val is None:
        warn("No value for '%s' found " % setting)
    return val

if __name__ == '__main__':
    (opt, flags, extra) = parser.parse(sys.argv[1:])
    if opt.debug:
        DEBUG = True
        debug('Activate debug')
    if not extra:
        parser.fatal('No subcommand given')
    cfs = parse_config()
    for s in SETTINGS:
        locals()[s] = set_setting(s, cfs, opt)
    if user is None or password is None:
        fatal('No username or password')
    sub = extra[0]
    if sub not in SUBS:
        options.fatal("invalid subcommand: " % sub)
    elif sub == CHECK:
        result = check(user, cfs['password'])
        if result is not None:
            print "The current balance for the account '%s' is: %s €" \
            % (user, result)
        else:
            fatal("Error checking balance")