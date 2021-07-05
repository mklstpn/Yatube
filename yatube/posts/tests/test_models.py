from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            text='Очень-оочень-ооочень-оооочень длинный тестовый текст',
            author=cls.author,
        )

        cls.group = Group.objects.create(
            title='Заголовок очень интересной группы',
            slug='test-group',
            description='test_group_description'
        )

    def test_post_text_field(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_title_field(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
