try:
    import cProfile as profile  # noqa: N813
except ImportError:
    import profile

import io
import pstats

from django.conf import settings


class ProfilerMiddleware(object):
    """
    Simple profile middleware to profile django views. To run it, add ?prof to
    the URL like this:

        http://localhost:8000/view/?prof

    Optionally pass the following to modify the output:

    ?sort => Sort the output by a given metric. Default is time.
        See http://docs.python.org/2/library/profile.html#pstats.Stats.sort_stats
        for all sort options.

    ?count => The number of rows to display. Default is 100.

    This is adapted from an example found here:
    http://www.slideshare.net/zeeg/django-con-high-performance-django-presentation.
    """

    def can(self, request):
        has_user = hasattr(request, "user")
        is_staff = False
        if has_user and request.user is not None and request.user.is_staff:
            is_staff = True

        return settings.DEBUG and "prof" in request.GET and (not has_user or is_staff)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if self.can(request):
            self.profiler = profile.Profile()
            args = (request,) + callback_args
            try:
                return self.profiler.runcall(callback, *args, **callback_kwargs)
            except Exception:
                # we want the process_exception middleware to fire
                # https://code.djangoproject.com/ticket/12250
                return

    def process_response(self, request, response):
        if self.can(request):
            self.profiler.create_stats()
            stream = io.StringIO()
            stats = pstats.Stats(self.profiler, stream=stream)
            stats.strip_dirs().sort_stats(request.GET.get("prof_sort", "time"))
            stats.print_stats(int(request.GET.get("prof_count", 100)))
            response.content = "<pre>%s</pre>" % stream.getvalue()
            response["content-type"] = "text/html"
        return response
