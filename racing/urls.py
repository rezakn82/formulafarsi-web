from django.urls import path
from .views import (
    drivers_list_view,
    driver_detail_view,
    teams_list_view,
    team_detail_view,
    standings_view,
)

app_name = 'racing'

urlpatterns = [
    path('standings/', standings_view, name='standings'),
    path('drivers/', drivers_list_view, name='drivers_list'),
    path('drivers/<str:code>/', driver_detail_view, name='driver_detail'),
    path('teams/', teams_list_view, name='teams_list'),
    path('teams/<int:pk>/', team_detail_view, name='team_detail'),
]