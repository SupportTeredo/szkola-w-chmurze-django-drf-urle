from django.contrib import admin

from .models import ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('code', 'original_url', 'created_at')
    search_fields = ('code', 'original_url')
