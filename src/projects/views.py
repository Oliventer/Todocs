from rest_framework import viewsets, status
from projects.models import Project, Collaboration
from users.models import User
from projects.serializer import ProjectSerializer, CollaborationSerializer
from rest_framework.response import Response
from projects.project_creator import ProjectCreator
from rest_framework.decorators import action
from projects.permission import IsProjectOwner
from rest_framework.permissions import IsAuthenticated


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
        return Collaboration.objects.filter(project__in=self.request.user.project_set.all()).order_by('pk')

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.action in ('transfer_ownership', 'update', 'partial_update', 'destroy'):
            permission_classes.append(IsProjectOwner)

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(pk=request.data['user'])
        project = Project.objects.get(pk=request.data['project'])

        if not Project.add_collaborator(request, user, project):
            return Response(status=status.HTTP_403_FORBIDDEN)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if not Project.edit_collaborator(user, request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        collaboration = Collaboration.objects.get(pk=kwargs['pk'])

        if not Project.remove_collaborator(request, collaboration):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'])
    def transfer_ownership(self, request, *args, **kwargs):
        another_user = self.get_object()
        owner = Collaboration.objects.get(user=request.user, project=another_user.project)

        if not Project.change_owner(owner, another_user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(another_user, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
