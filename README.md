# iLert plugin for checkmk

> Note: we suggest using the [native ilert checkmk plugin](https://docs.ilert.com/integrations/checkmk/native)

## Requirements

```sh
# install dependencies
apt-get install python-requests
```

## Plugin files

- `/omd/sites/cmk/local/share/check_mk/notifications/ilert` - python script to send checkmk events to iLert. In this repo is that `./ilert-check-mk.py`

- `/omd/sites/cmk/local/share/check_mk/web/plugins/wato/ilert.py` - python script to build GUI elements for the plugin
