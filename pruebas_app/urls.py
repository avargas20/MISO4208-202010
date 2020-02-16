from django.urls import path
from . import views
from django.conf.urls import url
from django.conf import settings

urlpatterns = [
    url(r'^$', views.home, name='home'),
]