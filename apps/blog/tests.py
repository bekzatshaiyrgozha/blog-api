from django.test import TestCase, Client, AsyncClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Post, PostStatus
from unittest.mock import patch


class BlogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.async_client = AsyncClient()
        User = get_user_model()
        self.user = User.objects.create_user(email="u@example.com", password="pass", first_name="A", last_name="B")
        self.cat = Category.objects.create(name="Tech", name_ru="Тех", name_kz="ТехKZ", slug="tech")
        self.post = Post.objects.create(author=self.user, title="P1", slug="p1", body="b", status=PostStatus.PUBLISHED, category=self.cat)

    def test_posts_list_language_aware(self):
        # request with Accept-Language ru
        resp_ru = self.client.get(reverse("posts-list"), HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(resp_ru.status_code, 200)
        data_ru = resp_ru.json()
        # paginated or list: handle both
        items = data_ru.get("results", data_ru)
        self.assertTrue(len(items) >= 1)
        name_ru = items[0].get("category", {}).get("name")
        self.assertIn(name_ru, ["Тех", "Tech"])  # prefer ru

        # request with Accept-Language en
        resp_en = self.client.get(reverse("posts-list"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(resp_en.status_code, 200)
        data_en = resp_en.json()
        items_en = data_en.get("results", data_en)
        name_en = items_en[0].get("category", {}).get("name")
        self.assertEqual(name_en, "Tech")

    @patch("apps.blog.views.httpx.AsyncClient")
    def test_stats_async(self, mock_client_cls):
        # Setup dummy async client
        class DummyResp:
            def __init__(self, status, data):
                self.status_code = status
                self._data = data

            def json(self):
                return self._data

        class DummyClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, url):
                if "open.er-api.com" in url:
                    return DummyResp(200, {"rates": {"KZT": 450.23, "RUB": 89.10, "EUR": 0.92}})
                if "timeapi.io" in url:
                    return DummyResp(200, {"dateTime": "2024-03-15T18:30:00+05:00"})

        mock_client_cls.return_value = DummyClient()

        # call async endpoint
        resp = self.async_client.get(reverse("api-stats"))
        result = resp.result()
        self.assertEqual(result.status_code, 200)
        body = result.json()
        self.assertIn("blog", body)
        self.assertIn("exchange_rates", body)
        self.assertEqual(body["exchange_rates"]["KZT"], 450.23)
import asyncio
from unittest.mock import patch, AsyncMock

from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory
from django.core.cache import cache
from django.conf import settings

from .views import stats
from .models import Post, PostStatus
from django.contrib.auth import get_user_model


class BlogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(email="tuser@example.com", password="pass1234", first_name="T", last_name="U")
        # create a published post
        Post.objects.create(author=self.user, title="P1", slug="p1", body="b", status=PostStatus.PUBLISHED)

    @patch("apps.blog.views.cache")
    def test_posts_list_cache_key_includes_language(self, mock_cache):
        # call list endpoint with ?lang=ru and ensure cache.set called with language-aware key
        resp = self.client.get("/api/posts/?lang=ru")
        # cache.set should be called at least once; inspect first call args
        self.assertTrue(mock_cache.set.called)
        key = mock_cache.set.call_args[0][0]
        self.assertIn("lang=ru", key)

    def test_stats_async_endpoint(self):
        # Mock external httpx AsyncClient to return predictable JSON
        class MockResp:
            def __init__(self, data, status=200):
                self._data = data
                self.status_code = status

            def json(self):
                return self._data

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, url):
                if "open.er-api" in url:
                    return MockResp({"rates": {"KZT": 450.0, "RUB": 89.1, "EUR": 0.92}})
                if "timeapi.io" in url:
                    return MockResp({"dateTime": "2024-03-15T18:30:00+05:00"})
                return MockResp({}, status=404)

        factory = APIRequestFactory()
        request = factory.get("/api/stats/")

        with patch("apps.blog.views.httpx.AsyncClient", MockClient):
            result = asyncio.run(stats(request))
            # result is a DRF Response
            self.assertEqual(result.status_code, 200)
            data = result.data
            self.assertIn("blog", data)
            self.assertIn("exchange_rates", data)
            self.assertEqual(data["exchange_rates"]["KZT"], 450.0)
from django.test import TestCase

# Create your tests here.
