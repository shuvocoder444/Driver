from django.utils import translation
from django.conf import settings


class PersistentLanguageMiddleware:
    """
    Guarantees 100% persistent language selection across all pages:
    Frontend, Admin, Dashboard, Driver Portal, and Visitor pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Check session first, then cookie, fallback to English
        lang_code = request.session.get('_language') or request.COOKIES.get('django_language') or 'en'
        
        if lang_code not in ['en', 'ru']:
            lang_code = 'en'

        # 2. Activate language in Django
        translation.activate(lang_code)
        request.LANGUAGE_CODE = lang_code
        request.session['_language'] = lang_code

        # 3. Process request
        response = self.get_response(request)

        # 4. Ensure cookie is always set so language never resets on browser restart
        response_lang_code = request.session.get('_language', lang_code)
        if request.COOKIES.get('django_language') != response_lang_code:
            response.set_cookie(
                'django_language',
                response_lang_code,
                max_age=365 * 24 * 3600,
                path='/',
                samesite='Lax'
            )

        return response
