from rest_framework import viewsets, status
from docs.models import Document, Attachment
from docs.serializer import DocumentSerializer, AttachmentSerializer
from docs.attachment_creator import AttachmentCreator
from rest_framework.response import Response


class DocumentViewset(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(project=self.kwargs['project_pk'])


class AttachmentViewset(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return Attachment.objects.filter(project=self.kwargs['project_pk'])

    def create(self, request, *args, **kwargs):
        serializer = AttachmentCreator(request.data['file'], request.data['project'])()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
