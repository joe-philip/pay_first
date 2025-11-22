import json

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from root.utils.constants.cache_keys import KEYS


class CacheFetchMiddleware(MiddlewareMixin):
    """
    Middleware to return cached response if available.
    Should be placed early in MIDDLEWARE list.
    """

    def process_request(self, request):

        # Only cache GET requests (idempotent)
        if request.method == "GET":

            if not request.path in KEYS:
                return None

            if authorization := request.headers.get("authorization"):
                token = authorization.split(" ")[1]
            else:
                token = "0"
            cache_key = f"cache-api-{token}-{KEYS[request.path]}"
            cached_response = cache.get(cache_key)

            if cached_response:
                # Rebuild HttpResponse object from cache
                return JsonResponse(json.loads(cached_response), safe=False)

        return None


class CacheStoreMiddleware(MiddlewareMixin):
    """
    Middleware to store successful responses into cache.
    Should be placed after all view middlewares.
    """

    def process_response(self, request, response):
        # Only cache GET responses with 200 status
        if request.method == "GET" and response.status_code == 200:
            if not request.path in KEYS:
                return response
            if isinstance(request.user, AnonymousUser):
                user_token = "0"
            else:
                user_token = str(request.user.auth_token.key)
            cache_key = f"cache-api-{user_token}-{KEYS[request.path]}"
            # Convert JsonResponse to JSON string
            try:
                content = response.content.decode()
                # cache permanently
                cache.set(cache_key, content, timeout=None)
            except Exception as e:
                print(f"[CacheStoreMiddleware] Failed to cache response: {e}")

        return response
