import shutil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


def post_correct_context(self, response):
    """Сравнение полей поста."""
    first_object = response.context['page'][0]
    object_text = first_object.text
    object_author = first_object.author
    object_group = first_object.group
    object_pub_date = first_object.pub_date
    object_image = first_object.image

    self.assertEqual(object_text, self.post.text)
    self.assertEqual(object_author, self.author)
    self.assertEqual(object_group, self.group)
    self.assertEqual(object_pub_date, self.post.pub_date)
    self.assertEqual(object_image, 'posts/small.gif')


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 'MEDIA_ROOT' отправлено в __init__.py
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user_views')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='test-test',
            description='super-mega-test-group',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.group_2 = Group.objects.create(
            title='second test group',
            slug='second-test-test',
            description='second-super-mega-test-group',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.author)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (
                reverse('groups', kwargs={'slug': self.group.slug})
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        post_correct_context(self, response)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_2.get(
            reverse('profile', kwargs={'username': self.author}))
        author_object = response.context['author']
        self.assertEqual(author_object, self.author)
        post_correct_context(self, response)

    def test_groups_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('groups', kwargs={'slug': self.group.slug})
        )
        response_object = response.context['group']
        post_correct_context(self, response)

        self.assertEqual(response_object.title, self.group.title)
        self.assertEqual(
            response_object.description, self.group.description)
        self.assertEqual(response_object.slug, self.group.slug)

    def test_single_post_detail_page_show_correct_context(self):
        """Шаблон отдельного поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.author, 'post_id': self.post.id})
        )
        response_object = response.context['post']
        self.assertEqual(response_object.text, self.post.text)
        self.assertEqual(response_object.group, self.group)
        self.assertEqual(response_object.author, self.author)
        self.assertEqual(response_object.pub_date, self.post.pub_date)
        self.assertEqual(response_object.image, 'posts/small.gif')

    def test_new_page_shows_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_page_shows_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client_2.get(
            reverse('post_edit',
                    kwargs={'username': self.author, 'post_id': self.post.id}))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_not_shown_in_other_group(self):
        """Пост не отображается на странице другой группы"""
        response = self.authorized_client.get(
            reverse('groups', kwargs={'slug': self.group_2.slug})
        )
        object = response.context['page']
        self.assertNotIn(self.post, object)

    def test_authorized_user_can_follow_other_user(self):
        """Авторизованный пользователь может подписаться"""
        self.follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('profile_follow', kwargs={
                    'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), self.follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.author).exists())

    def test_unauthorized_user_cant_follow_other(self):
        """Не авторизованный пользователь не может подписаться"""
        self.follow_count = Follow.objects.count()
        self.guest_client.get(
            reverse('profile_follow', kwargs={
                'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), self.follow_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.author
        ).exists())

    def test_new_post_appear_only_for_followers(self):
        """Новый пост появляется только у фолловеров"""
        Follow.objects.create(
            user=self.user, author=self.author)
        response = self.authorized_client.get(reverse('follow_index'))
        post_correct_context(self, response)

    def test_new_post_not_appear_for_unfollowers(self):
        """Новый пост не появляется только у неподписавшихся пользователей"""
        response = self.authorized_client.get(reverse('follow_index'))
        object = response.context['page']
        self.assertNotIn(self.post, object)

    def test_cache_index_check(self):
        cache.clear()
        new_post = Post.objects.create(
            text='Тестовый кеш',
            author=self.author,
            group=self.group,
        )
        response_clear = self.authorized_client.get(reverse('index'))
        test_post_clear = response_clear.context['page'][0]
        self.assertEqual(test_post_clear, new_post)
        Post.objects.filter(id=new_post.id).delete()
        response_cached = self.authorized_client.get(reverse('index'))
        test_post_cached = response_cached.context
        self.assertIsNone(test_post_cached)
        cache.clear()
        response_cleared = self.authorized_client.get(reverse('index'))
        test_post_cleared = response_cleared.context['page'][0]
        self.assertNotEqual(test_post_cleared, new_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='paginator_user')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-test',
            description='super-mega-test-group',
        )
        for posts in range(13):
            Post.objects.create(
                text=f'Тестовый текст {posts}',
                author=cls.author,
                group=cls.group,
            )

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_records(self):
        """10 постов на главной отображаются."""
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        """3 поста на главной отображаются."""
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_group_page_contains_ten_records(self):
        """10 постов на странице группы отображаются."""
        response = self.client.get(
            reverse('groups', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_group_page_contains_three_records(self):
        """3 поста на странице группы отображаются."""
        response = self.client.get(
            reverse('groups', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_profile_page_contains_five_records(self):
        """5 постов на первой странице профиля отображаются."""
        response = self.client.get(
            reverse('profile', kwargs={'username': self.author.username}))
        self.assertEqual(len(response.context.get('page').object_list), 5)

    def test_profile_second_page_contains_five_records(self):
        """5 постов на второй странице профиля отображаются."""
        response = self.client.get(
            reverse('profile',
                    kwargs={'username': self.author.username}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 5)

    def test_profile_third_page_contains_ten_records(self):
        """3 поста на третьей странице профиля отображаются."""
        response = self.client.get(
            reverse('profile',
                    kwargs={'username': self.author.username}) + '?page=3')
        self.assertEqual(len(response.context.get('page').object_list), 3)
