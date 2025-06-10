from django.db import models

# Create your models here.
class Announcement(models.Model):
    url = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)