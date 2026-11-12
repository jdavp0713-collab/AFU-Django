from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio),
    path("api/predict", views.identificar, name="identificar"),
    path("api/chat", views.preguntar, name="preguntar"),
]
