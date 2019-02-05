import unittest

import mock

from cors import preflight
from cors.utils import HeadersDict, Request


def _request(url="http://example.com", method="GET", headers=None, origin="http://example.com",
             **kwargs):
    request = mock.MagicMock(name="mock_request")
    request._response = mock.MagicMock()
    request.kwargs = {"_response": request._response}
    request.kwargs.update(kwargs)
    request.url = url
    request.method = method
    request.headers = HeadersDict(headers or {})
    request.prepare = lambda: request

    if "origin" not in request.headers:
        request.headers["origin"] = origin
    return request


def _response(request=None, headers=None):
    response = mock.MagicMock()
    response.request = request or _request()
    response.headers = HeadersDict(headers or {})
    return response


def _session():
    session = mock.MagicMock()

    def send(request):
        return getattr(request, "_response", mock.MagicMock())
    session.send = mock.MagicMock(wraps=send)
    return session


class Function_check_origin_Tests(unittest.TestCase):

    def test_same_origin(self):
        self.assertIsNone(preflight.check_origin(_response(), _request()))

    def test_different_origin(self):
        with self.assertRaises(preflight.AccessControlError) as context:
            preflight.check_origin(_response(), _request(origin="http://foo"))

        self.assertIn("not allowed", str(context.exception))

    def test_wildcard_origin(self):
        response = _response(headers={"Access-Control-Allow-Origin": "*"})
        request = _request(origin="http://foobar")

        self.assertIsNone(preflight.check_origin(response, request))


class Function_check_method_Tests(unittest.TestCase):
    def test_simple_methods(self):
        self.assertIsNone(preflight.check_method(_response(), _request(method="GET")))
        self.assertIsNone(preflight.check_method(_response(), _request(method="HEAD")))
        self.assertIsNone(preflight.check_method(_response(), _request(method="POST")))

    def test_non_simple_method(self):
        with self.assertRaises(preflight.AccessControlError) as context:
            preflight.check_method(_response(), _request(method="DELETE"))

        self.assertRegexpMatches(
            str(context.exception),
            "Method '.+' not allowed for resource '.*'")

    @staticmethod
    def test_allowed_method():
        headers = {"Access-Control-Allow-Methods": "PUT"}
        preflight_response = _response(headers=headers)
        prepared_request = _request(method="PUT")

        preflight.check_method(preflight_response, prepared_request)


class Function_check_headers_Tests(unittest.TestCase):
    def test_simple_headers(self):
        preflight.check_method(_response(), _request(headers={"Accept": "foo"}))
        preflight.check_method(_response(), _request(headers={"Content-Type": "application/json"}))

        with self.assertRaises(preflight.AccessControlError) as context:
            preflight.check_headers(
                _response(),
                _request(headers={"X-Auth-Token": "foo"}))

        self.assertRegexpMatches(
            str(context.exception),
            "Headers .* not allowed")

    def test_allowed_headers(self):
        response = _response(headers={"Access-Control-Allow-Headers": "X-Auth-Token"})
        request = _request(headers={"X-Auth-Token": "foo"})

        self.assertIsNone(preflight.check_headers(response, request))

    def test_post_simple_content_type(self):
        response = _response()
        request = _request(method="POST", headers={"Content-Type": "text/plain"})

        self.assertIsNone(preflight.check_headers(response, request))

    def test_post_content_types(self):
        response = _response()
        request = _request(method="POST", headers={"Content-Type": "application/json"})

        with self.assertRaises(preflight.AccessControlError) as context:
            preflight.check_headers(response, request)

        self.assertRegexpMatches(
            str(context.exception),
            "Headers .+ not allowed for resource '.*'")


class Function_prepare_preflight_allowed_origin_Tests(unittest.TestCase):
    def test_same_origin(self):
        request = _request()

        h, c = preflight.prepare_preflight_allowed_origin(request)

        self.assertEqual(h, {})
        self.assertEqual(c, [])

    def test_different_origin(self):
        request = _request(headers={"Origin": "http://foobar"})

        h, c = preflight.prepare_preflight_allowed_origin(request)

        self.assertEqual(h, {})
        self.assertEqual(c, [preflight.check_origin])


class Function_prepare_preflight_allowed_methods_Tests(unittest.TestCase):
    def test_simple_methods(self):
        request = _request(method="POST", headers={"Content-Type": "text/plain"})

        h, c = preflight.prepare_preflight_allowed_methods(request)

        self.assertEqual(h, {})
        self.assertEqual(c, [])

    def test_non_simple_method(self):
        request = _request(method="PUT")

        h, c = preflight.prepare_preflight_allowed_methods(request)

        self.assertEqual(h, {"Access-Control-Request-Method": "PUT"})
        self.assertEqual(c, [preflight.check_method])


class Function_prepare_preflight_allowed_headers_Tests(unittest.TestCase):
    def test_simple_headers(self):
        request = _request(headers={
            "Accept": "foo",
        })

        h, c = preflight.prepare_preflight_allowed_headers(request)

        self.assertEqual(h, {})
        self.assertEqual(c, [])

    def test_extra_headers(self):
        request = _request(headers={"Foo-Bar": "baz"})

        h, c = preflight.prepare_preflight_allowed_headers(request)

        self.assertEqual(h, {"Access-Control-Request-Headers": "Foo-Bar"})
        self.assertEqual(c, [preflight.check_headers])

    def test_unusual_content_type(self):
        request = _request(method="POST", headers={"Content-Type": "application/json"})

        h, c = preflight.prepare_preflight_allowed_headers(request)

        self.assertEqual(h, {"Access-Control-Request-Headers": "Content-Type"})
        self.assertEqual(c, [preflight.check_headers])


class Function_prepare_preflight_Tests(unittest.TestCase):
    def test_same_origin(self):
        request = _request()

        preflight_request, checks = preflight.prepare_preflight(request)

        self.assertIsNone(preflight_request)
        self.assertEqual(len(checks), 0)

    def test_other(self):
        request = _request(
            url="http://foo.bar.baz/qux",
            method="DELETE",
            headers={"Foo-bar": "baz/qux"})

        preflight_request, checks = preflight.prepare_preflight(request)

        self.assertIsInstance(preflight_request, Request)
        self.assertIn(preflight.check_origin, checks)
        self.assertIn(preflight.check_method, checks)
        self.assertIn(preflight.check_headers, checks)

    def test_options(self):
        request = _request(url="http://foo.bar.baz/qux", method="OPTIONS")

        preflight_request, _ = preflight.prepare_preflight(request)

        self.assertIsNone(preflight_request)


class Function_generate_acceptable_preflight_response_headers_Tests(unittest.TestCase):
    def setUp(self):
        self.method = preflight.generate_acceptable_preflight_response_headers

    def test_generate_headers_for_empty_preflight(self):
        headers = {}

        response = self.method(headers)

        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertNotIn("Access-Control-Allow-Methods", response)
        self.assertNotIn("Access-Control-Allow-Headers", response)

    def test_generate_headers_for_needed_method_and_header(self):
        headers = {
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Content-Type"
        }

        response = self.method(headers)

        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertEqual(response["Access-Control-Allow-Methods"], "PUT")
        self.assertEqual(response["Access-Control-Allow-Headers"], "Content-Type")


class Function_generate_acceptable_actual_response_headers_Tests(unittest.TestCase):
    def setUp(self):
        self.method = preflight.generate_acceptable_actual_response_headers

    def test_generate_headers_for_empty_response(self):
        headers = {}

        corsified = self.method(headers)

        self.assertEqual(corsified["Access-Control-Allow-Origin"], "*")
        self.assertNotIn("Access-Control-Allow-Methods", headers)
        self.assertNotIn("Access-Control-Allow-Headers", headers)

    def test_generate_headers_for_cross_origin(self):
        headers = {"Access-Control-Allow-Origin": "foo"}
        origin = "bar"

        corsified = self.method(headers, origin)

        self.assertEqual(corsified["Access-Control-Allow-Origin"], "*")

    def test_generate_headers_for_matched_origin(self):
        headers = {"Access-Control-Allow-Origin": "foo"}
        origin = "foo"

        corsified = self.method(headers, origin)

        self.assertEqual(corsified["Access-Control-Allow-Origin"], "foo")

    def test_generate_headers_for_extra_exposed_headers(self):
        headers = {
            "Access-Control-Expose-Headers": "foo, baz",
            "bar": "qux"
        }

        corsified = self.method(headers)

        exposed = corsified["Access-Control-Expose-Headers"].split(",")
        exposed = [h.strip() for h in exposed]
        self.assertIn("Foo", exposed)
        self.assertIn("Bar", exposed)
        self.assertIn("Baz", exposed)


# class EndToEndCORSTests(unittest.TestCase):
#     def setUp(self):
#         self.handler = lambda h: None
#         self.server = rester.mocks.mock_http_server(handler=lambda h: self.handler(h))
#         self.server.start()
#         self.addCleanup(self.server.stop)

#         self.host = "{address}:{port}".format(
#             **self.server.get_application().settings["_listen"])

#     def test_send(self):
#         request = requests.Request(
#             "GET", self.server.base_url, {"Origin": self.server.base_url.strip("/")}).prepare()

#         response = preflight.send(request)

#         self.assertTrue(response.ok)

#     def test_allowed_origin(self):
#         self.handler = mock.MagicMock(wraps=lambda h: (
#             h.set_header("Access-Control-Allow-Origin", "http://foobar"),
#         ))
#         request = requests.Request(
#             "GET", self.server.base_url, {"Origin": "http://foobar"}).prepare()

#         response = preflight.send(request)

#         self.assertTrue(response.ok)
#         self.assertEqual(self.handler.call_count, 2)

#     def test_origin_not_allowed(self):
#         request = requests.Request(
#             "GET", self.server.base_url, {"Origin": "http://foobar"}).prepare()

#         with self.assertRaises(preflight.AccessControlError) as context:
#             preflight.send(request)

#         self.assertRegexpMatches(
#             context.exception.message,
#             "Origin '.+' not allowed for resource '.+'")

#     def test_access_protected_header(self):
#         self.handler = lambda h: h.set_header("Foo-Bar", "baz")
#         request = requests.Request(
#             "GET", self.server.base_url, {"Origin": self.server.base_url.strip("/")}).prepare()

#         response = preflight.send(request)

#         self.assertIn("Foo-Bar", response.headers.keys())
#         with self.assertRaises(preflight.AccessControlError):
#             response.headers["Foo-Bar"]
