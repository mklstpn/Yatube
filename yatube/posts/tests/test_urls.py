from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='test-test',
            description='super-mega-test-group',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.author)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': '/',
            'new.html': '/new/',
            'group.html': '/group/test-test/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client_2.get(adress)
                self.assertTemplateUsed(response, template)

    def test_template_for_post_edit_page(self):
        """Проверка правильности шаблона редактирования поста."""
        template = 'new.html'
        adress = '/author/1/edit/'
        response = self.authorized_client_1.get(adress)
        self.assertTemplateUsed(response, template)

    def test_index_url_exists_at_desired_location(self):
        """Главная страница доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_url_exists_at_desired_location_authorized(self):
        """Страница /group/test-test/ доступна авторизованному
        пользователю."""
        response = self.authorized_client_2.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_url_exists_at_desired_location_unauthorized(self):
        """Страница /group/test-test/ доступна неавторизованному
        пользователю."""
        response = self.guest_client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_url_exists_at_desired_location_authorized(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client_2.get('/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_url_redirect_unauthorized(self):
        """Страница /new/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, f'{reverse("login")}?next=/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_username_url_exists_at_desired_location_unauthorized(self):
        """Страница /<username>/ доступна любому пользователю."""
        response = self.guest_client.get(
            f'/{self.author}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_username_post_id_url_exists_for_unauthorized(self):
        """Страница /<username>/<post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(
            f'/{self.author}/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location_anonimous(self):
        """Страница /<username>/<post_id>/edit/ недоступна анониму."""
        response = self.guest_client.get(
            f'/{self.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next=/{self.author}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location_author(self):
        """Страница /<username>/<post_id>/edit/ доступна автору поста."""
        response = self.authorized_client_1.get(
            f'/{self.author}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location_not_author(self):
        """Страница /<username>/<post_id>/edit/ не доступна не автору поста."""
        response = self.authorized_client_2.get(
            f'/{self.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, reverse(
            "post", kwargs={'username': self.author, 'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_redirect_not_permissions(self):
        """Страница /<username>/<post_id>/edit/ редиректит без прав доступа."""
        response = self.guest_client.get(
            f'/{self.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, (
            f'{reverse("login")}?next=/{self.author}/{self.post.id}/edit/'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_url_exists_at_desired_location_not_author(self):
        """Страница 404 отображается."""
        response = self.guest_client.get('/not-created-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
