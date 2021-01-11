from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class Perms(models.TextChoices):
    READ_ONLY = 'readonly'
    EDIT = 'edit'
    OWNER = 'owner'


def check_create_or_delete_conditions(request_user, project, access_level):
    try:
        Collaboration.objects.get(user=request_user,
                                  project=project,
                                  access_level='owner')
        return access_level != 'owner'
    except ObjectDoesNotExist:
        return False


def check_update_conditions(user, request):
    try:
        owner = Collaboration.objects.get(user=request.user,
                                          project=request.data['project'],
                                          access_level='owner')
        return request.data['access_level'] != 'owner' and user.pk != owner.pk
    except ObjectDoesNotExist:
        return False


def check_owner_perms(owner, another_user):
    try:
        Collaboration.objects.get(user=owner.user,
                                  project=owner.project,
                                  access_level='owner')
        return owner.project == another_user.project and owner.pk != another_user.pk
    except ObjectDoesNotExist:
        return False


class Project(models.Model):
    name = models.CharField(max_length=128)
    users = models.ManyToManyField('users.User', through='Collaboration')
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def change_owner(owner, another_user):
        if check_owner_perms(owner, another_user):
            owner.access_level = 'edit'
            owner.save()
            another_user.access_level = 'owner'
            another_user.save()
            return True
        return False

    @staticmethod
    def edit_collaborator(requested_user, request):
        if check_update_conditions(requested_user, request):
            requested_user.access_level = request.data['access_level']
            requested_user.save()
            return True
        return False

    @staticmethod
    def add_collaborator(request, user, project):
        if check_create_or_delete_conditions(request.user, project, request.data['access_level']):
            mdl = Collaboration(user=user, project=project, access_level=request.data['access_level'])
            mdl.save()
            return True
        return False

    @staticmethod
    def remove_collaborator(request, collaboration):
        if check_create_or_delete_conditions(request.user, collaboration.project, collaboration.access_level):
            collaboration.delete()
            return True
        return False


class Collaboration(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    access_level = models.TextField(choices=Perms.choices)
