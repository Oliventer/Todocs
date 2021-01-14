from projects.models import Project, Collaboration, Perms
from rest_framework import serializers
from users.serializer import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    users = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Project
        fields = ['pk', 'name', 'users', 'created']


class ProjectChangeOwnerSerializer(serializers.Serializer):
    demote_to = serializers.ChoiceField([('readonly', 'Read Only'), ('edit', 'Edit')])


class ProjectUpdateSerializer(serializers.Serializer):
    access_level = serializers.ChoiceField([('readonly', 'Read Only'), ('edit', 'Edit')])


class CurrentUserProjectsRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        return Project.objects.filter(collaboration__user=user, collaboration__access_level=Perms.OWNER)


class CollaborationSerializer(serializers.ModelSerializer):
    access_level = serializers.ChoiceField([('readonly', 'Read Only'), ('edit', 'Edit')])
    project = CurrentUserProjectsRelatedField()

    class Meta:
        model = Collaboration
        fields = ['pk', 'project', 'user', 'access_level']
