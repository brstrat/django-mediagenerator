from .settings import DEV_MEDIA_URL, MEDIA_DEV_MODE, DEV_CACHE_MEDIA
# Only load other dependencies if they're needed
if MEDIA_DEV_MODE:
    from .utils import _refresh_dev_names, _backend_mapping
    from django.http import HttpResponse, Http404
    from django.utils.cache import patch_cache_control
    from django.utils.http import http_date
    import time

    _REFRESH_DEV_NAMES_DONE_AT = 0	


TEXT_MIME_TYPES = (
    'application/x-javascript',
    'application/xhtml+xml',
    'application/xml',
)

class MediaMiddleware(object):
    """
    Middleware for serving and browser-side caching of media files.

    This MUST be your *first* entry in MIDDLEWARE_CLASSES. Otherwise, some
    other middleware might add ETags or otherwise manipulate the caching
    headers which would result in the browser doing unnecessary HTTP
    roundtrips for unchanged media.
    """

    MAX_AGE = 60 * 60 * 24 * 365

    def process_request(self, request):
        if not MEDIA_DEV_MODE:
            return


        """
        from mediagenerator.cache_store import MediageneratorCacheStore
        cache_store = MediageneratorCacheStore.check()

        logging.info(cache_store)

        if not cache_store:
            _refresh_dev_names()
            MediageneratorCacheStore.set(True)

        
        global DEV_CACHE_MEDIA

        logging.info("Cache status %s", DEV_CACHE_MEDIA)
        

        if _REFRESH_DEV_NAMES and DEV_CACHE_MEDIA:
            _refresh_dev_names()
            _REFRESH_DEV_NAMES_DONE_AT = time.time()
            _REFRESH_DEV_NAMES = False
        """
        global _REFRESH_DEV_NAMES_DONE_AT

        if (_REFRESH_DEV_NAMES_DONE_AT + 3) < time.time():
            _refresh_dev_names()
            _REFRESH_DEV_NAMES_DONE_AT = time.time()
        
        if not request.path.startswith(DEV_MEDIA_URL):
            return

        filename = request.path[len(DEV_MEDIA_URL):]

        try:
            backend = _backend_mapping[filename]
        except KeyError:
            raise Http404('The mediagenerator could not find the media file "%s"'
                          % filename)
        content, mimetype = backend.get_dev_output(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        if mimetype.startswith('text/') or mimetype in TEXT_MIME_TYPES:
            mimetype += '; charset=utf-8'
        response = HttpResponse(content, content_type=mimetype)
        response['Content-Length'] = len(content)

        # Cache manifest files MUST NEVER be cached or you'll be unable to update
        # your cached app!!!
        if response['Content-Type'] != 'text/cache-manifest' and \
                response.status_code == 200:
            patch_cache_control(response, public=True, max_age=self.MAX_AGE)
            response['Expires'] = http_date(time.time() + self.MAX_AGE)
        return response
