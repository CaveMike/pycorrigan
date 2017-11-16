from webapp2 import Route

class ContentRoute(Route):
    def __init__(self, template, handler=None, name=None, defaults=None,
                 build_only=False, handler_method=None, methods=None,
                 schemes=None, header=None, header_values=()):
        self.header = header
        self.header_values = header_values
        return super(ContentRoute, self).__init__(template, handler, name, defaults,
                 build_only, handler_method, methods, schemes)

    def match(self, request):
        #print 'req', request
        results = super(ContentRoute, self).match(request)
        if not results:
            #print 'no match'
            return None

        if self.header:
            #print 'expected', self.header
            try:
                header_value = request.headers[self.header]
                #print 'have'
            except KeyError:
                #print 'dont have'
                return None

            if not header_value:
                #print 'dont have'
                return None

            #print 'expected', self.header_values
            #print 'have', header_value
            if not any(hv in header_value for hv in self.header_values):
                #print 'no match'
                return None

        #print 'match'

        (route, args, kwargs) = results
        return self, args, kwargs

