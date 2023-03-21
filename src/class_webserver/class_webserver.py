from aiohttp import ClientSession, web
from functools import partial

def handler(obj, method, request):
    print("object={} ::: method={} ::: request={}".format(obj, method, request))
    return web.json_response(getattr(obj,method)())

def class_webserver(objects):
    app = web.Application()

    for obj in objects:
        prefix = '' if hasattr(obj, 'prefix') == False else obj.prefix
        methods = [ method for method in dir(obj) if callable(getattr(obj, method)) ]

        for method in methods:
            if method.startswith('get_'):
                path = '{}/{}'.format(prefix,method.replace('get_',''))
                app.router.add_get(path, partial(handler, obj, method))

    web.run_app(app, port=8001)
