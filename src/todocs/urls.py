"""todocs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from projects.views import ProjectViewset, CollaborationViewset
from users.views import UserViewset
from docs.views import DocumentViewset, AttachmentViewset


router = DefaultRouter()
router.register('projects', ProjectViewset)
router.register('collaborations', CollaborationViewset, basename='Collaborations')
router.register('users', UserViewset)
# router.register('documents', DocumentViewset)
#router.register('attachments', AttachmentViewset)

docs_router = NestedDefaultRouter(router, 'projects', lookup='project')
docs_router.register('documents', DocumentViewset, basename='project-documents')
docs_router.register('attachments', AttachmentViewset, basename='project-attachments')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(docs_router.urls)),
    path('auth/', include('rest_framework.urls'))
]
