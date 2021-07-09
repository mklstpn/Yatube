import shutil
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='editor')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='big.gif',
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

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Форма добавляет новый пост."""
        uploaded = SimpleUploadedFile(
            name='bigol.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_get = Post.objects.get(pk=2)
        self.assertEqual(post_get.text, form_data['text'])
        self.assertEqual(post_get.group, self.group)
        self.assertEqual(post_get.image.name, f'posts/{uploaded.name}')

    def test_edit_post(self):
        """Форма проверяет редактирование поста."""
        self.posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированый текст',
            'group': self.group.id,
        }

        response = self.authorized_client.post(
            reverse(('post_edit'), kwargs={'username': self.author,
                                           'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTrue(
            Post.objects.filter(
                id=1,
                text='Отредактированый текст',
                author=self.author, group=self.group,
                image='posts/big.gif'
            ).exists()
        )

    def test_authorized_user_can_add_comment(self):
        """Форма проверяет добавление коммента."""
        form_data = {
            'text': 'Текст комментария',
        }

        response = self.authorized_client.post(
            reverse(('add_comment'), kwargs={'username': self.author,
                                             'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTrue(
            Comment.objects.filter(
                post=self.post.id,
                author=self.author,
                text='Текст комментария',
            ).exists()
        )

    def test_unauthorized_user_can_not_add_comment(self):
        """Форма проверяет добавление коммента."""
        self.comment_count = Comment.objects.count()

        form_data = {
            'text': 'Текст неавторизованного комментария',
        }

        response = self.guest_client.post(
            reverse(('add_comment'), kwargs={'username': self.author,
                                             'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), self.comment_count)

        self.assertFalse(
            Comment.objects.filter(
                post=self.post.id,
                author=self.author,
                text='Текст неавторизованного комментария',
            ).exists()
        )
