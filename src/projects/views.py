from rest_framework import viewsets, status
from projects.models import Project, Collaboration
from projects.serializer import ProjectSerializer, CollaborationSerializer, ProjectChangeOwnerSerializer, ProjectUpdateSerializer
from rest_framework.response import Response
from projects.project_creator import ProjectCreator
from rest_framework.decorators import action
from projects.permission import IsProjectOwner
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch


class ProjectViewset(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, *args, **kwargs):
        serializer = ProjectCreator(request.data['name'], request.user)()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CollaborationViewset(viewsets.ModelViewSet):
    serializer_class = CollaborationSerializer

    def get_queryset(self):
        return Collaboration.objects.filter(project__in=self.request.user.project_set.all())\
            .order_by('pk').prefetch_related(Prefetch('project', Project.objects.filter(users=self.request.user)))

    def get_serializer_class(self):
        if self.action == "update":
            return ProjectUpdateSerializer
        elif self.action == "transfer_ownership":
            return ProjectChangeOwnerSerializer
        return CollaborationSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.action in ('transfer_ownership', 'update', 'partial_update', 'destroy'):
            permission_classes.append(IsProjectOwner)

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.validated_data['project']
        project.add_collaborator(serializer.validated_data['user'], serializer.validated_data['access_level'])

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        collaboration_for_update = self.get_object()

        serializer = self.get_serializer(collaboration_for_update, data=request.data)
        serializer.is_valid(raise_exception=True)

        access_level_for_update = serializer.validated_data['access_level']
        collaboration_for_update.project.edit_collaborator(collaboration_for_update.user, access_level_for_update)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        collaboration = self.get_object()
        collaboration.project.remove_collaborator(collaboration.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'], serializer_class=ProjectChangeOwnerSerializer)
    def transfer_ownership(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collaboration = self.get_object()
        demote_to = serializer.validated_data['demote_to']

        collaboration.project.change_owner(collaboration, demote_to)
        return Response(serializer.data, status=status.HTTP_200_OK)
