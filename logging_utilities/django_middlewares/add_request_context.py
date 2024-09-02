from logging_utilities.thread_context import thread_context


class AddToThreadContextMiddleware(object):
    """Django middleware that stores request to thread local variable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(thread_context, 'request', request)
        response = self.get_response(request)
        setattr(thread_context, 'request', None)
        return response
