#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import socket

import cmk.gui.config as config
from cmk.gui.i18n import _

from cmk.gui.valuespec import (
    CascadingDropdown,
    Dictionary,
    DropdownChoice,
    TextUnicode,
    TextAscii,
    Transform,
)

from cmk.gui.plugins.wato import (
    notification_parameter_registry,
    NotificationParameter,
    passwordstore_choices,
)

from cmk.gui.plugins.wato.utils import (
    PasswordFromStore,)


# We have to transform because 'add_to_event_context'
# in modules/events.py can't handle complex data structures
def transform_back_html_mail_url_prefix(p):
    if isinstance(p, tuple):
        return {p[0]: p[1]}
    if p == "automatic_http":
        return {"automatic": "http"}
    if p == "automatic_https":
        return {"automatic": "https"}
    return {"manual": p}


def transform_forth_html_mail_url_prefix(p):
    if not isinstance(p, dict):
        return ("manual", p)

    k, v = list(p.items())[0]
    if k == "automatic":
        return "%s_%s" % (k, v)

    return ("manual", v)


def local_site_url():
    return "http://" + socket.gethostname() + "/" + config.omd_site() + "check_mk/"


def _get_url_prefix_specs(default_choice, default_value="automatic_https"):

    return Transform(CascadingDropdown(
        title=_("URL prefix for links to Check_MK"),
        help=_("If you use <b>Automatic HTTP/s</b>, the URL prefix for host "
               "and service links within the notification is filled "
               "automatically. If you specify an URL prefix here, then "
               "several parts of the notification are armed with hyperlinks "
               "to your Check_MK GUI. In both cases, the recipient of the "
               "notification can directly visit the host or service in "
               "question in Check_MK. Specify an absolute URL including the "
               "<tt>.../check_mk/</tt>."),
        choices=[
            ("automatic_http", _("Automatic HTTP")),
            ("automatic_https", _("Automatic HTTPs")),
            ("manual", _("Specify URL prefix"),
             TextAscii(
                 regex="^(http|https)://.*/check_mk/$",
                 regex_error=_("The URL must begin with <tt>http</tt> or "
                               "<tt>https</tt> and end with <tt>/check_mk/</tt>."),
                 size=64,
                 default_value=default_choice,
            )),
        ],
        default_value=default_value),
        forth=transform_forth_html_mail_url_prefix,
        back=transform_back_html_mail_url_prefix)


@notification_parameter_registry.register
class NotificationIlert(NotificationParameter):
    @property
    def ident(self):
        return "ilert"

    @property
    def spec(self):
        return Dictionary(
            title=_("Create notification with the following parameters"),
            optional_keys=[
                'url_prefix', 'ilert_priority', 'ilert_summary_host', 'ilert_summary_service'
            ],
            elements=[
                ("ilert_api_key",
                 CascadingDropdown(title=_("iLert alert source API key"),
                                   help=_("API key for iLert alert server"),
                                   choices=[(
                                       "ilert_api_key",
                                       _("API key"),
                                       TextAscii(size=80, allow_empty=False),
                                   ),
                     ("store", _("API key from password store"),
                                       DropdownChoice(sorted=True,
                                                      choices=passwordstore_choices))])),
                ("ilert_priority",
                 DropdownChoice(
                     sorted=True,
                     choices=[
                         ("high", _("High (with escalation)")),
                         ('low', _("Low (without escalation")),
                     ],
                     title=_("Notifcation priority (This will overrride the priority configured in the alert source)"
                             ),
                     default_value='high')),
                ("ilert_summary_host",
                 TextUnicode(
                     title=_("Custom incident summary for host alerts"),
                     default_value="$NOTIFICATIONTYPE$ Host Alert: $HOSTNAME$ is $HOSTSTATE$ - $HOSTOUTPUT$",
                     size=64,
                 )),
                ("ilert_summary_service",
                 TextUnicode(
                     title=_("Custom incident summary for service alerts"),
                     default_value="$NOTIFICATIONTYPE$ Service Alert: $HOSTALIAS$/$SERVICEDESC$ is $SERVICESTATE$ - $SERVICEOUTPUT$",
                     size=64,
                 )),
                ("url_prefix", _get_url_prefix_specs(local_site_url,
                                                     default_value="automatic_https")),
            ],
        )
