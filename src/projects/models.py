from django.db import models, transaction


class Perms(models.TextChoices):
    READ_ONLY = 'readonly'
    EDIT = 'edit'
    OWNER = 'owner'


class OwnerMutationError(Exception):
    pass


class Project(models.Model):
    name = models.CharField(max_length=128)
    users = models.ManyToManyField('users.User', through='Collaboration')
    created = models.DateTimeField(auto_now_add=True)

    def change_owner(self, new_owner_collaboration: 'projects.Collaboration', demote_to: Perms):
        current_owner_collaboration = Collaboration.objects.get(project=self,
                                                                access_level=Perms.OWNER)
        with transaction.atomic():
            current_owner_collaboration.access_level = demote_to
            current_owner_collaboration.save()

            new_owner_collaboration.access_level = Perms.OWNER
            new_owner_collaboration.save()

    def edit_collaborator(self, user: 'users.User', new_access_level: Perms):
        owner = Collaboration.objects.get(project=self, access_level=Perms.OWNER)
        user_to_update = Collaboration.objects.get(user=user, project=self)

        if owner == user_to_update:
            raise OwnerMutationError

        user_to_update.access_level = new_access_level
        user_to_update.save()

    def add_collaborator(self, user: 'users.User', access_level: Perms):
        owner = Collaboration.objects.get(project=self, access_level=Perms.OWNER)
        user_to_create = Collaboration(user=user, project=self, access_level=access_level)

        if owner.access_level == user_to_create.access_level:
            raise OwnerMutationError

        user_to_create.save()

    def remove_collaborator(self, user: 'users.User'):
        owner = Collaboration.objects.get(project=self, access_level=Perms.OWNER)
        user_to_delete = Collaboration.objects.get(user=user, project=self)

        if owner == user_to_delete:
            raise OwnerMutationError

        user_to_delete.delete()


class Collaboration(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    access_level = models.TextField(choices=Perms.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'project'], name='unique collaboration')
        ]
