from django.db import models

# Create your models here.

class Message(models.Model):
    sender = models.CharField(max_length=100)
    recipient = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField('date sent')

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} at {self.timestamp}"
