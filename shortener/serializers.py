from urllib.parse import urlparse

from rest_framework import serializers

from .models import ShortURL


class ShortURLSerializer(serializers.ModelSerializer):
    url = serializers.URLField(write_only=True, max_length=2048)
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortURL
        fields = ('code', 'original_url', 'url', 'short_url')
        read_only_fields = ('code', 'original_url', 'short_url')

    def validate_url(self, value):
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https'):
            raise serializers.ValidationError(
                'Adres musi używać protokołu HTTP lub HTTPS.'
            )
        if not parsed.netloc:
            raise serializers.ValidationError('Adres musi zawierać nazwę hosta.')
        return value

    def get_short_url(self, obj):
        path = f'/shrt/{obj.code}/'
        request = self.context.get('request')
        return request.build_absolute_uri(path) if request else path

