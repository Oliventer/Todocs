import pytest
from rest_framework.test import APIClient
from mixer.backend.django import mixer
from docs.attachment_creator import AttachmentCreator
from docs.models import Attachment, Document

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def attachment():
    return mixer.blend('docs.Attachment')


@pytest.fixture
def project():
    return mixer.blend('projects.Project')


def test_attachment_creator_service(attachment):
    obj = Attachment.objects.get(pk=1)
    AttachmentCreator(obj.file, obj.project.pk)()
    assert Attachment.objects.last().file == obj.file


def test_nested_attachment(api):
    request = api.get('/api/v1/projects/1/attachments/')
    assert request.status_code == 200


def test_nested_documents(api):
    request = api.get('/api/v1/projects/1/documents/')
    assert request.status_code == 200


def test_document_model_choicefields(api, project):
    bad_doc = api.post('/api/v1/projects/1/documents/', {'type': 'test', 'text': 'test', 'project': project.pk})
    assert bad_doc.status_code == 400


def test_file_storage(attachment):
    assert attachment.file.path == f'C:\\Users\\AOKov\\PycharmProjects\\todocs\\files\\{attachment.file}'


