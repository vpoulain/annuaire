from django.views.generic import TemplateView
from django.conf.urls import url, include

from . import views


urlpatterns = [
    url(r'^s3direct/', include('s3direct.urls')),
    url(r'^submission/', views.submit_project, name='submission'),
    url(r'^projects/(?P<pk>[0-9]+)$', views.ProjectDetailView.as_view(), name='project'),
    url(r'^projects', views.ProjectIndexView.as_view(), name='projects'),
    url(r'', TemplateView.as_view(template_name="app/index.html"), name='home')
]
