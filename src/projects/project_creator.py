from projects.serializer import ProjectSerializer
from projects.models import Collaboration


class ProjectCreator:
    def __init__(self, name, owner):
        self.owner = owner
        self.data = {
            'name': name,
        }

    def __call__(self):
        serializer = ProjectSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.create_collaborator(serializer.instance)

        return serializer

    def create_collaborator(self, serializer_instance):
        mdl = Collaboration(project=serializer_instance, user=self.owner, access_level='owner')
        mdl.save()
