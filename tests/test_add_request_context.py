import unittest

from django.conf import settings
from django.test import RequestFactory

from logging_utilities.django_middlewares.add_request_context import \
    AddToThreadContextMiddleware
from logging_utilities.thread_context import thread_context

if not settings.configured:
    settings.configure()


class AddToThreadContextMiddlewareTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_add_request(self):

        def test_handler(request):
            r_from_var = getattr(thread_context, 'request', None)
            self.assertEqual(request, r_from_var)

        request = self.factory.get("/some_path?test=some_value")
        middleware = AddToThreadContextMiddleware(test_handler)
        middleware(request)
