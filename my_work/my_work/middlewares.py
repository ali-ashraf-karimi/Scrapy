import urllib


class ForceUTF8ResponseMiddleware(object):

    """A downloader middleware to force utf8 encoding for all responses."""

    def process_response(self, request, response, spider):
        spider_needs_utf8 = getattr(spider, "force_utf8", False)
        if not spider_needs_utf8:
            # Nothing for us to do here. Return original response.
            return response
        ubody = response.body_as_unicode().encode('utf8')
        return response.replace(body=ubody, encoding='utf8')


class FixMalformedUrlMiddleware(object):

    """A downloader middleware to fix urls having a query string with a missing root '/'.
       Will change this "http://www.domain.com?q=querystring" to this "http://www.domain.com/?q=querystring"
    """

    def process_request(self, request, spider):
        spider_needs_urlfix = getattr(spider, "fix_url", False)

        if not spider_needs_urlfix:
            # Nothing for us to do here.
            return
        parse_result = urllib.parse.urlparse(request.url)
        if not parse_result.path and parse_result.query:
            return request.replace(url=request.url.replace("?", "/?"))

        return
