import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')

        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDown()

    def test_create_post(self):
        """Проверка создания нового поста."""
        form_data = {
            'text': 'Тестовый текст поста',
            'group': self.group.id,
            'image': self.uploaded
        }

        PostCreateFormTests.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        new_post = Post.objects.first()
        posts_fields = {
            new_post.text: form_data['text'],
            new_post.group.id: form_data['group'],
            new_post.image.name: f'posts/{form_data["image"].name}'
        }

        for field, expected in posts_fields.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected, 'Новая запись не создана')

    def test_edit_post(self):
        """Проверка изменения поста."""
        post = Post.objects.create(
            text='Тестовый текст поста',
            author=PostCreateFormTests.user,
            group=self.group
        )
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание группы 2'
        )

        form_data = {
            'text': 'Новый текст поста',
            'group': new_group.id,
            'image': self.uploaded
        }

        PostCreateFormTests.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        changed_post = Post.objects.latest('text', 'group', 'image')
        posts_fields = {
            changed_post.text: form_data['text'],
            changed_post.group.id: form_data['group'],
            changed_post.image: f'posts/{form_data["image"].name}'
        }

        for field, expected in posts_fields.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected, 'Запись не изменена')


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def setUp(self):
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        self.post = Post.objects.create(
            text='Тестовый текст поста',
            author=CommentCreateFormTests.user,
            group=self.group
        )

    def test_denied_comment_for_guest_client(self):
        """Проверка запрета комментариев для неавторизованного пользователя."""
        form_data = {'text': 'Тестовый комментарий'}

        CommentCreateFormTests.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        response = CommentCreateFormTests.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        obj = response.context['comments']

        self.assertNotIn(comment,
                         obj,
                         'Ошибка: комментарий неавторизованного пользователя')

    def test_exist_comment_on_post_page(self):
        """Проверка создания комментария на странице поста."""
        form_data = {'text': 'Тестовый комментарий'}

        CommentCreateFormTests.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        response = CommentCreateFormTests.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        obj = response.context['comments']

        self.assertIn(comment,
                      obj,
                      'Комментарий не размещен')
