from django.db import models

# Create your models here.
class Document(models.Model):
    file = models.FileField(upload_to='uploads/') #Le fichier va etre stocke dans le dossier fields
    #title = models.CharField(max_length=100, null=True, blank=True)

class FileUpload(models.Model):
    file = models.FileField(upload_to='upload/')
    def __str__(self):
        return f"File Upload: {self.file.name}"