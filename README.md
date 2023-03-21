###

# py_class_webserver

## Description

py_class_webserver exposes a function `class_webserver` which takes a list of
objects.  For each object, any functions that have an http verb prefix 
(`get_`, `delete_`, `put_`, `post_`) will be registered as an http path with
path parameters for each function argument.  Once all functions have been
registered, an aiohttp webserver will be started to serve those verb paths.

## Installation

```
python3 -m pip install  git+https://github.com/rhhayward/py_class_webserver.git@master
```

## Usage

```
from class_webserver import class_webserver

class with_param_and_body:
    def __init__(self):
        pass
    def post_with_param_and_body(self, param=None, body_object=None):
        return "with_param_and_body:param={}:object={}".format(param, body_object)

class_webserver([
        with_param_and_body(),
    ])

```

Running this will result in:

```
<with_param_and_body> registered path post:</with_param_and_body/param/{param:.*}/>
======== Running on http://0.0.0.0:8001 ========
(Press CTRL+C to quit)
```

And running curl on that endpoint will result in

```
$ curl localhost:8001/with_param_and_body/param/test/ --data '{"object":"value"}'
"with_param_and_body:param=test:object=value"
```
