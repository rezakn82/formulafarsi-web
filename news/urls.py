from django.urls import path, re_path
from .views import home_view, article_detail_view

app_name = 'news'

urlpatterns = [
    path('', home_view, name='home'),
    re_path(r'^news/(?P<slug>[-\w]+)/$', article_detail_view, name='article_detail'),
]