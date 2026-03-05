from django.urls import path
from .views import VTaskPListView

urlpatterns = [
    path('vtaskp/', VTaskPListView.as_view(), name='vtaskp-list'),
]

