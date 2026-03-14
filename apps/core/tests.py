from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from apps.core.middleware import UserLanguageTimezoneMiddleware

User = get_user_model()


class UserLanguageTimezoneMiddlewareTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		# MiddlewareMixin requires a get_response callable in newer Django versions
		self.middleware = UserLanguageTimezoneMiddleware(get_response=lambda req: None)

	def test_user_language_has_priority(self):
		user = User.objects.create_user(email="u1@example.com", password="pass1234", first_name="A", last_name="B")
		user.language = "ru"
		user.timezone = "UTC"
		user.save()

		request = self.factory.get("/")
		request.user = user
		self.middleware.process_request(request)
		self.assertEqual(request.LANGUAGE_CODE, "ru")

	def test_query_param_over_accept_language(self):
		# ?lang= has higher priority than Accept-Language
		request = self.factory.get("/?lang=en", HTTP_ACCEPT_LANGUAGE="ru")
		# anonymous user
		request.user = type("Anon", (), {"is_authenticated": False})()
		self.middleware.process_request(request)
		self.assertEqual(request.LANGUAGE_CODE, "en")

	def test_accept_language_used_when_no_user_or_query(self):
		# use 'kz' since settings.LANGUAGES uses 'kz' for Kazakh
		request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="kz,ru;q=0.8")
		request.user = type("Anon", (), {"is_authenticated": False})()
		self.middleware.process_request(request)
		# first value from Accept-Language should be chosen
		self.assertEqual(request.LANGUAGE_CODE, "kz")
