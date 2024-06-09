import time

from aiohttp import ClientSession, web
from functools import partial
from inspect import signature
from concurrent.futures import ThreadPoolExecutor, TimeoutError

ALLOW_BACKGROUND = 'allowBackground'
PARALLELISM = 'parallelism'
STATUS_COMPLETED = 'completed'
STATUS_NOTFOUND = 'notfound'
STATUS_RUNNING = 'running'
TIMEOUT = 'timeout'

DEFAULT_PARALLELISM = 10
DEFAULT_TIMEOUT = 0.100

### This works for a single server, but what about multiple servers?
class SingleServerBackgroundExecutor():

    def __init__(self, options):
        self.parallelism = options[PARALLELISM] if PARALLELISM in options else DEFAULT_PARALLELISM
        self.threadPoolExecutor = ThreadPoolExecutor(self.parallelism)
        self.timeout = options[TIMEOUT] if TIMEOUT in options else DEFAULT_TIMEOUT
        self.executionIds = {}

    def submit(self, f):
        future = self.threadPoolExecutor.submit(f)
        executionId = str( round(time.time()*1000) )
        self.executionIds[executionId] = future
        return executionId

    ### returns (result, status)
    def getResult(self,executionId):
        if executionId in self.executionIds:
            future = self.executionIds[executionId]
            try:
                result = future.result(timeout=self.timeout)
                del self.executionIds[executionId]
                return result, STATUS_COMPLETED
            except TimeoutError as te:
                return None, STATUS_RUNNING
        else:
            return None, STATUS_NOTFOUND

class ClassWebserver():
    def __init__(self, options):
        self.allowBackground = options[ALLOW_BACKGROUND] if ALLOW_BACKGROUND in options else False
        self.backgroundExecutor = SingleServerBackgroundExecutor(options) if self.allowBackground is True else None

    async def handler(self, obj, method, request, options={}):
        ### handler will pull params from request to execute obj.method()
        try:
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

            if self.allowBackground is False:
                result = f()
                return self.formatResult(result)
            else:
                execution_id = self.backgroundExecutor.submit(f)
                result, status = self.backgroundExecutor.getResult(execution_id)
                if status == STATUS_COMPLETED:
                    return self.formatResult(result)
                elif status == STATUS_RUNNING:
                    return web.json_response({'id':execution_id,'href':f'/execution/{execution_id}'}, status=202 )
                elif status == STATUS_NOTFOUND:
                    return web.HTTPNotFound()

        except Exception as e:
            print("had Exception e={}".format(e))
            return web.HTTPInternalServerError()

    def formatResult(self, result):
        if isinstance(result, (bytes, bytearray)):
            return web.Response(body=result)
        return web.json_response(result)

    def getMethods(self, obj):
        ### getMethods returns list of object methods
        return [ method for method in dir(obj) if callable(getattr(obj, method)) ]

    def getPath(self, obj, method):
        ### getPath builds up an http path for a given obj.method(),
        ###    first obj.prefix, if present, then the method name sans
        ###    http verb, then for each method argument that doesn't
        ###    start with 'body_', a path parameter in format
        ###    `/param_name/{param_name:.*}`.
        fragment = self.stripVerb(method)
        path = r'/{}'.format(fragment) if hasattr(obj, 'prefix') == False else r'/{}/{}'.format(obj.prefix, fragment)

        for param in signature(getattr(obj, method)).parameters:
            if param.startswith('body_') == False:
                format = '{' + param + ':.*}'
                path += '/{}/{}'.format(param, format)
        return path

    def stripVerb(self, m):
        ### stripVerb returns string, stripped of http verb prefix, if
        ###    present.
        verb = self.getVerb(m)
        if verb != None:
            return m.replace('{}_'.format(verb),'',1)
        else:
            return m

    def getVerb(self, m):
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

    def checkExecution(self, request ):
        execution_id = request.match_info.get('execution_id', None)
        result, status = self.backgroundExecutor.getResult(execution_id)

        if status == STATUS_COMPLETED:
            return self.formatResult(result)
        elif status == STATUS_RUNNING:
            return web.json_response({'id':execution_id,'href':f'/execution/{execution_id}'}, status=202 )
        elif status == STATUS_NOTFOUND:
            return web.HTTPNotFound()

    def serve(self, objects, port):
        app = web.Application()

        if self.allowBackground is True:
            app.add_routes([ web.route('get', '/execution/{execution_id:.*}', self.checkExecution) ])
            print("added route for /execution/{execution_id:.*}")

        for obj in objects:
            methods = self.getMethods(obj)

            for method in methods:
                verb = self.getVerb(method)
                if verb != None:
                    path = self.getPath(obj, method)
                    print("<{}> registered path {}:<{}>".format(obj.__class__.__name__, verb, path))
                    app.add_routes([ web.route(verb, path, partial(self.handler, obj, method)) ])

        web.run_app(app, port=port)

def serve(objects, port=8001, options={}):
    ### class_webserver takes a list of objects, and for each object
    ###    sets up a path for each method that begins with an http verb
    ###    (get, delete, post, put).  It sets up method arguments as
    ###    http path parameters.  Finally, it

    ce = ClassWebserver(options)
    ce.serve(objects, port)
