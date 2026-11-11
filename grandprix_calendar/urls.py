from django.urls import path
from .views import calendar_view, grandprix_detail_view

app_name = 'grandprix_calendar'

urlpatterns = [
    path('', calendar_view, name='calendar_list'),
    path('round-<int:round_number>/', grandprix_detail_view, name='grandprix_detail'),
]