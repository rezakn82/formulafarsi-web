from django.urls import path, re_path
from .views import home_view, article_detail_view, articles_list_view, global_search_view

app_name = 'news'

urlpatterns = [
    path('', home_view, name='home'),
    path('search/', global_search_view, name='global_search'),
    path('news/', articles_list_view, name='articles_list'),
    re_path(r'^news/(?P<slug>[-\w]+)/$', article_detail_view, name='article_detail'),
]