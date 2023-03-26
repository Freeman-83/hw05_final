from django.shortcuts import render
from http import HTTPStatus


def page_not_found(request, exception):
    template = 'core/404.html'
    return render(request,
                  template,
                  {'path': request.path},
                  status=HTTPStatus.NOT_FOUND)


def server_error(request):
    template = 'core/500.html'
    return render(request,
                  template,
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)


def permission_denied(request, exception):
    template = 'core/403.html'
    return render(request,
                  template,
                  status=HTTPStatus.FORBIDDEN)


def csrf_failure(request, reason=''):
    template = 'core/403csrf.html'
    return render(request, template)
