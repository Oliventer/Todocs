import pytest
from rest_framework.test import APIClient
from mixer.backend.django import mixer
from projects.project_creator import ProjectCreator
from projects.models import Project, Collaboration, Perms, OwnerMutationError
from projects.permission import IsProjectOwner
from projects.views import CollaborationViewset
from django.db.utils import IntegrityError

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user():
    return mixer.blend('users.User', email='aliventer@gmail.com')


@pytest.fixture()
def another_user():
    return mixer.blend('users.User')


@pytest.fixture
def project():
    return mixer.blend('projects.Project')


@pytest.fixture
def owner_collaboration(api, user, project):
    return Collaboration.objects.create(user=user, project=project, access_level='owner')


@pytest.fixture
def member_collaboration(project):
    return mixer.blend(Collaboration, project=project, access_level='edit')


def test_project_creator_service(user):
    ProjectCreator('vasya', user)()
    last = Collaboration.objects.last()
    assert Project.objects.last().name == 'vasya'
    assert last.user == user and last.access_level == 'owner'


def test_collaboration_model_choicefields(api, user, project):
    api.force_authenticate(user=user)
    bad_collaboration = api.post('/api/v1/collaborations/', {'user': user, 'project': project, 'access_level': 'test'})
    assert bad_collaboration.status_code == 400


def test_transfer_ownership_endpoint(api, owner_collaboration):
    api.force_authenticate(user=owner_collaboration.user)
    request = api.get('/api/v1/collaborations/1/transfer_ownership/')
    assert request.status_code == 405


def test_unauthorized_user_cant_use_api(api):
    assert api.get('/api/v1/collaborations/').status_code == 403


def test_user_cant_get_collaborations_with_another_project(api, owner_collaboration):
    mixer.blend(Collaboration, access_level='edit')
    api.force_authenticate(user=owner_collaboration.user)
    request = api.get('/api/v1/collaborations/2/')
    assert Collaboration.objects.filter(pk=2).exists()
    assert request.status_code == 404


def test_change_owner(owner_collaboration, member_collaboration):
    member_collaboration.project.change_owner(member_collaboration, Perms.EDIT)
    assert member_collaboration.access_level == Perms.OWNER
    assert Collaboration.objects.get(user=owner_collaboration.user).access_level == Perms.EDIT


def test_edit_collaborator(owner_collaboration, member_collaboration):
    member_collaboration.project.edit_collaborator(member_collaboration.user, Perms.READ_ONLY)
    assert Collaboration.objects.get(user=member_collaboration.user).access_level == Perms.READ_ONLY


def test_owner_cant_edit_himself(owner_collaboration, member_collaboration):
    with pytest.raises(OwnerMutationError):
        member_collaboration.project.edit_collaborator(owner_collaboration.user, Perms.READ_ONLY)


def test_add_collaborator(owner_collaboration, another_user):
    owner_collaboration.project.add_collaborator(another_user, Perms.READ_ONLY)
    assert Collaboration.objects.last().user == another_user


def test_add_owner_collaboration(owner_collaboration, another_user):
    with pytest.raises(OwnerMutationError):
        owner_collaboration.project.add_collaborator(another_user, Perms.OWNER)


def test_remove_collaborator(owner_collaboration, member_collaboration):
    owner_collaboration.project.remove_collaborator(member_collaboration.user)
    with pytest.raises(Collaboration.DoesNotExist):
        Collaboration.objects.get(user=member_collaboration.user)


def test_remove_owner_collaborator(owner_collaboration):
    with pytest.raises(OwnerMutationError):
        owner_collaboration.project.remove_collaborator(owner_collaboration.user)


def test_owner_have_is_project_owner_permission(api, owner_collaboration, member_collaboration):
    request = api.get('/collaborations/1/')
    request.user = owner_collaboration.user
    perms = IsProjectOwner.has_object_permission(IsProjectOwner, request, CollaborationViewset, member_collaboration)
    assert perms is True


def test_member_do_not_have_project_owner_permission(api, owner_collaboration, member_collaboration):
    request = api.get('/collaborations/1/')
    request.user = member_collaboration.user
    perms = IsProjectOwner.has_object_permission(IsProjectOwner, request, CollaborationViewset, member_collaboration)
    assert perms is False


def test_is_project_owner_permission_owner_do_not_have_permissions_for_own_instance(api, owner_collaboration):
    request = api.get('/collaborations/1/')
    request.user = owner_collaboration.user
    perms = IsProjectOwner.has_object_permission(IsProjectOwner, request, CollaborationViewset, owner_collaboration)
    assert perms is False


def test_collaborations_unique_constraint(owner_collaboration):
    with pytest.raises(IntegrityError):
        collaboration = Collaboration(user=owner_collaboration.user,
                                      project=owner_collaboration.project,
                                      access_level=Perms.READ_ONLY)
        collaboration.save()
