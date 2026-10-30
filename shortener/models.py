from django.db import models


class ShortURL(models.Model):
    original_url = models.URLField(max_length=2048, unique=True)
    code = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} -> {self.original_url}'
