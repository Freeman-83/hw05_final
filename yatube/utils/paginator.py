from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(request, obj):
    paginator = Paginator(obj, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
