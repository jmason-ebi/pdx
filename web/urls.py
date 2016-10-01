"""web URL Configuration"""

from django.conf.urls import include,url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

	url(r'^$', views.index, name='index'),
    url(r'^pdx/(?P<pk>\w{0,50})/$', views.pdx, name="pdx"),
    url(r'^search/', views.search, name="search"),
    #url(r'^search/', include('haystack.urls')),
    url(r'^resources/', views.resources, name="resources"),
]

