#!/usr/bin/env python


# iLert Check_MK Native Plugin
#
# Copyright (c) 2013-2020, iLert GmbH. <support@ilert.com>
# All rights reserved.


import os
import syslog
import fcntl
import urllib
import uuid
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr
import argparse
import io
import sys
import datetime

PLUGIN_VERSION = "1.0"


def log(level, message):
    sys.stdout.write("%s %s %s\n" %
                     (datetime.datetime.now().isoformat(), level, message))


def create_and_send(endpoint, port, apiKey, payload):
    xml_doc = create_xml(payload)
    send(endpoint, port, apiKey, xml_doc)


def send(endpoint, port, apiKey, xml):
    log("INFO", "Sending event to iLert...")
    headers = {"Content-type": "application/xml", "Accept": "application/xml"}
    url = "%s:%s/api/v1/events/checkmk/%s" % (endpoint, port, apiKey)

    try:
        req = urllib.request.Request(url, str.encode(xml), headers)
        urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log("WARNING", "too many requests, will try later. Server response: %s" % e.read())
            exit(1)
        elif 400 <= e.code <= 499:
            log("WARNING", "event not accepted by iLert. Reason: %s" % e.read())
        else:
            log("ERROR", "could not send event to iLert. HTTP error code %s, reason: %s, %s" % (
                e.code, e.reason, e.read()))
            exit(1)
    except urllib.error.URLError as e:
        log("ERROR", "could not send event to iLert. Reason: %s\n" % e.reason)
        exit(1)
    except Exception as e:
        log("ERROR", "an unexpected error occurred. Please report a bug. Cause: %s %s" % (
            type(e), e.args))
        exit(1)
    else:
        log("INFO", "Event has been sent to iLert")


def create_xml(payload):
    xml_doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><event><payload>'

    for entry in payload:
        xml_doc += "<entry key=%s>%s</entry>" % (
            quoteattr(entry), str(escape(payload[entry])))

    xml_doc += "</payload></event>"

    log("INFO", xml_doc)
    return xml_doc


def main():
    parser = argparse.ArgumentParser(
        description='send events from CheckMK to iLert')
    parser.add_argument(
        '-a', '--apikey', help='API key for the alert source in iLert')
    parser.add_argument('-e', '--endpoint', default='https://api.ilert.com',
                        help='iLert API endpoint (default: %(default)s)')
    parser.add_argument('-p', '--port', type=int, default=443,
                        help='endpoint port (default: %(default)s)')
    parser.add_argument('--version', action='version', version=PLUGIN_VERSION)
    parser.add_argument('payload', nargs=argparse.REMAINDER,
                        help='event payload as key value pairs in the format key1=value1 key2=value2 ...')
    args = parser.parse_args()

    # populate payload data from environment variables
    payload = dict(PLUGIN_VERSION=PLUGIN_VERSION)
    for env in os.environ:
        if "NOTIFY_" in env:
            payload[env] = os.environ[env]

    # ... and payload specified via command line
    for arg in args.payload:
        if arg:
            a = arg.split('=', 1)
            if a and a[0] and a[1]:
                payload.update({a[0]: a[1]})

    if args.apikey is not None:
        apikey = args.apikey
    elif 'CONTACTPAGER' in payload:
        apikey = payload['CONTACTPAGER']
    else:
        apikey = None

    if apikey is None:
        log("ERROR", "parameter apikey is required in save mode and must be provided either via command line or in the pager field of the contact definition in CheckMK")
        exit(1)
    create_and_send(args.endpoint, args.port, apikey, payload)

    exit(0)


if __name__ == '__main__':
    main()
