from rest_framework import permissions
from projects.models import Collaboration


class IsProjectOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        try:
            q = Collaboration.objects.get(user=request.user, project=obj.project, access_level='owner')
            return q.pk != obj.pk
        except Collaboration.DoesNotExist:
            return False
