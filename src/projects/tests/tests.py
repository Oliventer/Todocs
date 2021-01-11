import pytest
from rest_framework.test import APIClient
from mixer.backend.django import mixer
from projects.project_creator import ProjectCreator
from projects.models import Project, Collaboration
from django.core.exceptions import ObjectDoesNotExist

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user():
    return mixer.blend('users.User', email='aliventer@gmail.com')


@pytest.fixture
def project():
    return mixer.blend('projects.Project')


@pytest.fixture
def owner_collaboration(user, project):
    return Collaboration.objects.create(user=user, project=project, access_level='owner')


@pytest.fixture
def member_collaboration(project):
    return mixer.blend(Collaboration, project=project, access_level='edit')


@pytest.fixture
def post_member_collaboration(api, owner_collaboration, member_collaboration):
    request = api.post('/collaborations/')
    request.data = {'user': member_collaboration.user,
                    'project': member_collaboration.project,
                    'access_level': 'edit'}

    request.user = owner_collaboration.user
    return request


@pytest.fixture
def put_member_collaboration(api, member_collaboration, owner_collaboration):
    request = api.put('/collaborations/1/')
    request.data = {'user': member_collaboration.user,
                    'project': member_collaboration.project,
                    'access_level': 'readonly'}
    request.user = owner_collaboration.user
    return request


@pytest.fixture
def put_owner_collaboration(api, owner_collaboration):
    request = api.put('/collaborations/1/')
    request.data = {'user': owner_collaboration.user,
                    'project': owner_collaboration.project,
                    'access_level': 'readonly'}
    request.user = owner_collaboration.user
    return request


@pytest.fixture()
def random_member_collaboration():
    return mixer.blend(Collaboration, access_level='edit')


def test_project_creator_service(user):
    ProjectCreator('vasya', user)()
    last = Collaboration.objects.last()
    assert Project.objects.last().name == 'vasya'
    assert last.user == user and last.access_level == 'owner'


def test_owner_cant_transfer_ownership_to_himself(owner_collaboration):
    change_owner = Project.change_owner(owner_collaboration, owner_collaboration)
    assert change_owner is False


def test_change_owner(owner_collaboration, member_collaboration):
    change_owner = Project.change_owner(owner_collaboration, member_collaboration)
    assert change_owner is True
    assert owner_collaboration.access_level == 'edit'
    assert member_collaboration.access_level == 'owner'


def test_owner_cant_transfer_ownership_to_user_from_another_project(owner_collaboration, random_member_collaboration):
    change_owner = Project.change_owner(owner_collaboration, random_member_collaboration)
    assert change_owner is False
    assert owner_collaboration.access_level == 'owner'
    assert random_member_collaboration.access_level == 'edit'


def test_member_cant_transfer_ownership(member_collaboration, owner_collaboration):
    change_owner = Project.change_owner(member_collaboration, owner_collaboration)
    assert change_owner is False
    assert member_collaboration.access_level == 'edit'
    assert owner_collaboration.access_level == 'owner'


def test_edit_collaborator(put_member_collaboration, member_collaboration):
    update = Project.edit_collaborator(member_collaboration, put_member_collaboration)
    assert update is True
    assert member_collaboration.access_level == 'readonly'


def test_owner_cant_edit_himself(owner_collaboration, put_owner_collaboration):
    update = Project.edit_collaborator(owner_collaboration, put_owner_collaboration)
    assert update is False
    assert owner_collaboration.access_level != 'readonly'


def test_owner_cant_edit_another_user_to_owner(put_member_collaboration, member_collaboration):
    put_member_collaboration.data['access_level'] = 'owner'
    update = Project.edit_collaborator(member_collaboration, put_member_collaboration)
    assert update is False
    assert member_collaboration.access_level != 'owner'


def test_member_cant_edit_another_members(owner_collaboration, put_owner_collaboration, member_collaboration):
    put_owner_collaboration.user = member_collaboration.user
    update = Project.edit_collaborator(owner_collaboration, put_owner_collaboration)
    assert update is False
    assert owner_collaboration.access_level != 'readonly'


def test_collaboration_model_choicefields(api, user, project):
    api.force_authenticate(user=user)
    bad_collaboration = api.post('/api/v1/collaborations/', {'user': user, 'project': project, 'access_level': 'test'})
    assert bad_collaboration.status_code == 400


def test_owner_cant_add_owner_collaboration(post_member_collaboration, member_collaboration):
    post_member_collaboration.data['access_level'] = 'owner'
    post = Project.add_collaborator(post_member_collaboration,
                                    post_member_collaboration.data['user'], post_member_collaboration.data['project'])
    assert post is False
    with pytest.raises(ObjectDoesNotExist):
        Collaboration.objects.get(user=post_member_collaboration.data['user'],
                                  project=post_member_collaboration.data['project'], access_level='owner')


def test_owner_can_add_collaborator(post_member_collaboration):
    post_member_collaboration.data['access_level'] = 'readonly'
    post = Project.add_collaborator(post_member_collaboration,
                                    post_member_collaboration.data['user'], post_member_collaboration.data['project'])
    assert post is True
    assert Collaboration.objects.get(user=post_member_collaboration.data['user'],
                                     project=post_member_collaboration.data['project'],
                                     access_level=post_member_collaboration.data['access_level'])


def test_member_cant_add_collaborator(api, member_collaboration, random_member_collaboration):
    request = api.post('/collaborations/')
    request.data = {'user': random_member_collaboration.user,
                    'project': random_member_collaboration.project, 'access_level': 'readonly'}
    request.user = member_collaboration.user

    post = Project.add_collaborator(request, request.data['user'],
                                    request.data['project'])
    assert post is False
    with pytest.raises(ObjectDoesNotExist):
        Collaboration.objects.get(user=request.data['user'], project=request.data['project'],
                                  access_level=request.data['access_level'])


def test_remove_collaborator(api, member_collaboration, owner_collaboration):
    request = api.delete('/collaborations/1')
    request.user = owner_collaboration.user
    delete = Project.remove_collaborator(request, member_collaboration)
    assert delete is True
    assert member_collaboration.pk is None


def test_owner_cant_remove_himself(api, owner_collaboration):
    request = api.delete('/collaborations/1')
    request.user = owner_collaboration.user
    delete = Project.remove_collaborator(request, owner_collaboration)
    assert delete is False
    assert owner_collaboration.pk is not None


def test_member_cant_delete_another_members(api, random_member_collaboration, member_collaboration):
    request = api.delete('/collaborations/1')
    request.user = member_collaboration.user
    delete = Project.remove_collaborator(request, random_member_collaboration)
    assert delete is False
    assert random_member_collaboration.pk is not None


def test_transfer_ownership_endpoint(api, owner_collaboration):
    api.force_authenticate(user=owner_collaboration.user)
    request = api.get('/api/v1/collaborations/1/transfer_ownership/')
    assert request.status_code == 405


def test_unauthorized_user_cant_use_api(api, owner_collaboration):
    assert api.get('/api/v1/collaborations/1/').status_code == 403


def test_user_cant_get_collaborations_with_another_project(api, owner_collaboration, random_member_collaboration):
    api.force_authenticate(user=owner_collaboration.user)
    request = api.get('/api/v1/collaborations/2/')
    assert Collaboration.objects.filter(pk=2).exists()
    assert request.status_code == 404
