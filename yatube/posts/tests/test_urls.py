from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Follow, Group, Post, User

INDEX = reverse('posts:index')
CREATE = reverse('posts:post_create')
GROUP = reverse('posts:group_list',
                kwargs={'slug': settings.SLUG})
PROFILE = reverse('posts:profile',
                  kwargs={'username': settings.USER_NAME})


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Созданим запись в БД для проверки доступности
        # адреса user/test-slug/
        cls.author = User.objects.create(username=settings.USER_NAME)
        cls.group = Group.objects.create(
            title=settings.GROUP_TITLE,
            slug=settings.SLUG,
            description=settings.DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=settings.POST_TEXT,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_guest_urls(self):
        # Проверяем общедоступные страницы
        urls_names = {
            INDEX: HTTPStatus.OK.value,
            GROUP: HTTPStatus.OK.value,
            PROFILE: HTTPStatus.OK.value,
            f'/posts/{self.post.pk}/': HTTPStatus.OK.value,
            '/unexisting_page/': HTTPStatus.NOT_FOUND.value,
        }
        for address, status in urls_names.items():
            with self.subTest(status=status):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status)

    def test_url_to_template(self):
        # Проверка соответсвия url и template
        urls_template = {
            INDEX: 'posts/index.html',
            GROUP: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            CREATE: 'posts/create_post.html',
        }
        for address, template in urls_template.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_autorized_urls(self):
        # Проверяем страницы доступные автору поста
        urls_names = {
            f'/posts/{self.post.pk}/edit/': HTTPStatus.OK.value,
            CREATE: HTTPStatus.OK.value,
        }
        for address, status in urls_names.items():
            with self.subTest(status=status):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_edit_no_author(self):
        # Проверка редактирования поста не автором
        response = self.client.get(
            f"/posts/{self.post.pk}/edit/")
        self.assertRedirects(response, (
            f'/auth/login/?next=/posts/{self.post.pk}/edit/'))

    # Проверяем статус 404 для авторизованного пользователя
    def test_task_list_url_redirect_anonymous(self):
        # Страница /unexisting_page/ не существует.
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404(self):
        # Страница 404 отдает кастомный шаблон
        # для неавторизованного потльзователя
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_follow_url(self):
        # тестирование подписчиков
        author = User.objects.create_user(username='author')
        response = self.authorized_client.get(
            f'/profile/{author.username}/follow/'
        )
        self.assertRedirects(response, f'/profile/{author.username}/')

    def test_unfollow_url(self):
        author = User.objects.create_user(username='author')
        Follow.objects.create(
            user=self.author,
            author=author
        )
        response = self.authorized_client.get(
            f'/profile/{author.username}/unfollow/'
        )
        self.assertRedirects(response, f'/profile/{author.username}/')
