from docs.serializer import AttachmentSerializer


class AttachmentCreator:
    def __init__(self, file, project):
        self.data = {
            'file': file,
            'file_name': str(file.name),
            'project': project
        }

    def __call__(self):
        serializer = AttachmentSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return serializer
