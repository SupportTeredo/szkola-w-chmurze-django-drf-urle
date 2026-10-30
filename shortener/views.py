from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .hashing import generate_code
from .models import ShortURL
from .serializers import ShortURLSerializer

MAX_ATTEMPTS = 5


def _get_or_create_short_url(original_url: str) -> tuple[ShortURL, bool]:
    """Zwraca (obiekt, czy_utworzono) dla podanego adresu URL."""
    existing = ShortURL.objects.filter(original_url=original_url).first()
    if existing:
        return existing, False

    for _ in range(MAX_ATTEMPTS):
        code = generate_code(
            original_url,
            lambda candidate: ShortURL.objects.filter(code=candidate).exists(),
        )
        try:
            with transaction.atomic():
                return ShortURL.objects.create(original_url=original_url, code=code), True
        except IntegrityError:
            # Równoległy request mógł zapisać ten sam URL albo zająć kod.
            existing = ShortURL.objects.filter(original_url=original_url).first()
            if existing:
                return existing, False

    raise IntegrityError('Nie udało się zapisać skróconego adresu URL.')


@api_view(['POST'])
def shorten_url(request: Request) -> Response:
    serializer = ShortURLSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    short_url, created = _get_or_create_short_url(serializer.validated_data['url'])
    data = ShortURLSerializer(short_url, context={'request': request}).data
    return Response(
        data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['GET'])
def resolve_url(request: Request, code: str) -> Response:
    short_url = get_object_or_404(ShortURL, code=code)
    return Response({'url': short_url.original_url})


def redirect_url(request: HttpRequest, code: str) -> HttpResponseRedirect:
    short_url = get_object_or_404(ShortURL, code=code)
    return redirect(short_url.original_url)
