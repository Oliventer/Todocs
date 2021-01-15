from django.db import models
from django_hashedfilenamestorage.storage import HashedFilenameFileSystemStorage


fs = HashedFilenameFileSystemStorage(location='../files')


class FileType(models.TextChoices):
    DOCS = 'DOC'
    MARKDOWN = 'MD'


class Document(models.Model):
    type = models.TextField(choices=FileType.choices)
    text = models.TextField()
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class Attachment(models.Model):
    file = models.FileField(storage=fs)
    file_name = models.TextField(max_length=256)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
