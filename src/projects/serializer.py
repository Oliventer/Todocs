from projects.models import Project, Collaboration
from rest_framework import serializers
from users.serializer import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    users = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Project
        fields = ['pk', 'name', 'users', 'created']


class CollaborationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collaboration
        fields = ['pk', 'project', 'user', 'access_level']
