from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Post, User

INDEX = reverse('posts:index')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(username=settings.USER_NAME)
        cls.post = Post.objects.create(
            text=settings.POST_TEXT,
            author=cls.test_user,
        )

    def test_page_correct_template(self):
        """Кэширование данных"""
        response = self.client.get(INDEX)
        cached_response_content = response.content
        Post.objects.create(text='Второй пост', author=self.test_user)
        response = self.client.get(INDEX)
        self.assertEqual(cached_response_content, response.content)
        cache.clear()
        response = self.client.get(INDEX)
        self.assertNotEqual(cached_response_content, response.content)
