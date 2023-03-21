from aiohttp import ClientSession, web
from functools import partial
from inspect import signature

async def handler(obj, method, request):
    ### handler will pull params from request to execute obj.method()
    jsonObject = None
    f = getattr(obj,method)
    for param in signature(f).parameters:
        if param.startswith('body_'):
            name = param.replace('body_','')
            if jsonObject == None:
                jsonObject = await request.json()
            f = partial(f, jsonObject[name])
        else:
            f = partial(f, request.match_info.get(param, None))
    return web.json_response(f())

def getMethods(obj):
    ### getMethods returns list of object methods
    return [ method for method in dir(obj) if callable(getattr(obj, method)) ]

def getPath(obj, method):
    ### getPath builds up an http path for a given obj.method(),
    ###    first obj.prefix, if present, then the method name sans
    ###    http verb, then for each method argument that doesn't
    ###    start with 'body_', a path parameter in format
    ###    `/param_name/{param_name:.*}/`.
    prefix = '' if hasattr(obj, 'prefix') == False else obj.prefix
    path = r'{}/{}/'.format(prefix, stripVerb(method))

    for param in signature(getattr(obj, method)).parameters:
        if param.startswith('body_') == False:
            format = '{' + param + ':.*}'
            path += '{}/{}/'.format(param, format)
    return path

def stripVerb(m):
    ### stripVerb returns string, stripped of http verb prefix, if
    ###    present.
    verb = getVerb(m)
    if verb != None:
        return m.replace('{}_'.format(verb),'',1)
    else:
        return m

def getVerb(m):
    ### getVerb returns http verb prefix if present, else None
    if m.startswith('get_'):
        return 'get'
    elif m.startswith('delete_'):
        return 'delete'
    elif m.startswith('put_'):
        return 'put'
    elif m.startswith('post_'):
        return 'post'
    else:
        return None

def class_webserver(objects, port=8001):
    ### class_webserver takes a list of objects, and for each object
    ###    sets up a path for each method that begins with an http verb
    ###    (get, delete, post, put).  It sets up method arguments as
    ###    http path parameters.  Finally, it
    app = web.Application()

    for obj in objects:
        methods = getMethods(obj)

        for method in methods:
            verb = getVerb(method)
            if verb != None:
                path = getPath(obj, method)
                print("<{}> registered path {}:<{}>".format(obj.__class__.__name__, verb, path))
                app.add_routes([ web.route(verb, path, partial(handler, obj, method)) ])

    web.run_app(app, port=port)
