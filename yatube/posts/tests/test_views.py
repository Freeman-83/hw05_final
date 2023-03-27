import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Follow, Group, Post

COUNT_POSTS: int = 15
POSTS_ON_LAST_PAGE: int = COUNT_POSTS % settings.POSTS_ON_PAGE
NUMBER_LAST_PAGE: int = (COUNT_POSTS // settings.POSTS_ON_PAGE) + 1

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        self.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                          b'\x01\x00\x80\x00\x00\x00\x00\x00'
                          b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                          b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                          b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                          b'\x0A\x00\x3B')

        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Тестовый текст поста',
            author=PostPagesTests.user,
            group=self.group,
            image=self.uploaded
        )

        cache.clear()

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDown()

    def get_comparison_values(self, dict_compared_values):
        """Вспомогательная функция для проверки словаря значений"""
        for obj, value in dict_compared_values.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj,
                                 value,
                                 f'Значения {obj} и {value} не совпадают')

    def get_comparison_post_context(self, obj):
        """Функция проверки контекста объекта post"""
        post_context = {obj.author: self.post.author,
                        obj.pub_date: self.post.pub_date,
                        obj.text: self.post.text,
                        obj.pk: self.post.id,
                        obj.group: self.post.group,
                        obj.image: self.post.image}
        self.get_comparison_values(post_context)

    def test_pages_uses_correct_template(self):
        """Проверка соответствия URL-имен и шаблонов."""
        reverse_names_templates = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for name, template in reverse_names_templates.items():
            with self.subTest(name=name):
                response = PostPagesTests.auth_client.get(name)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'URL-name {name} ожидает шаблон {template}'
                )

    def test_home_page_correct_context(self):
        """Проверка словаря контекста главной страницы."""
        response = PostPagesTests.auth_client.get(reverse('posts:index'))
        obj = response.context['page_obj'][0]
        self.get_comparison_post_context(obj)

    def test_group_list_correct_context(self):
        """Проверка словаря контекста страницы группы."""
        response = PostPagesTests.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        obj_group = response.context['group']
        self.get_comparison_values(
            {obj_group.title: self.group.title,
             obj_group.description: self.group.description}
        )
        obj_post = response.context['page_obj'][0]
        self.get_comparison_post_context(obj_post)

    def test_profile_correct_context(self):
        """Проверка словаря контекста страницы пользователя."""
        response = PostPagesTests.auth_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        obj_author = response.context['author']
        self.get_comparison_values(
            {obj_author: self.post.author,
             obj_author.posts.count(): self.post.author.posts.count()}
        )
        obj_post = response.context['page_obj'][0]
        self.get_comparison_post_context(obj_post)

    def test_post_detail_correct_context(self):
        """Проверка словаря контекста страницы поста."""
        response = PostPagesTests.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        obj_post_choice = response.context['post_choice']
        self.get_comparison_post_context(obj_post_choice)

    def test_create_edit_post_correct_context(self):
        """
        Проверка словаря контекста страниц создания и редактирования поста.
        """
        reverse_names = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        ]

        for name in reverse_names:
            response = PostPagesTests.auth_client.get(name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField
            }

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(
                        form_field,
                        expected,
                        f'Тип поля {value} не соответствует ожидаемому'
                    )

    def test_exist_created_post_on_pages(self):
        """
        Проверка нового поста
        на главной, групповой, пользовательской страницах.
        """
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author})
        ]

        for name in reverse_names:
            response = PostPagesTests.auth_client.get(name)
            obj = response.context['page_obj']
            self.assertIn(self.post,
                          obj,
                          'Запись на нужной странице отсутствует ')

    def test_new_post_not_exists_on_else_group(self):
        """
        Проверка отсутствия на странице группы поста без группы
        или из другой группы.
        """
        new_post = Post.objects.create(
            text='Тестовый текст нового поста',
            author=PostPagesTests.user
        )

        response = PostPagesTests.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        obj = response.context['page_obj']
        self.assertNotIn(new_post,
                         obj,
                         f'Страница группы {self.group}'
                         ' должна содержать записи только этой группы')

    def test_cache(self):
        """Проверка корректного кэширования данных главной страницы."""
        response_before_del = PostPagesTests.auth_client.get(
            reverse('posts:index')
        )
        response_before_del.context['page_obj'][0].delete()

        response_after_del = PostPagesTests.auth_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response_before_del.content,
                         response_after_del.content,
                         'Ошибка кэша')

        cache.clear()

        response_after_cache_clear = PostPagesTests.auth_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_before_del.content,
                            response_after_cache_clear.content,
                            'Ошибка удаления записи')


class FollowCreateTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_1 = User.objects.create_user(username='auth_user_1')
        cls.user_2 = User.objects.create_user(username='auth_user_2')
        cls.author = User.objects.create_user(username='author')

        cls.auth_client_1 = Client()
        cls.auth_client_1.force_login(cls.user_1)

        cls.auth_client_2 = Client()
        cls.auth_client_2.force_login(cls.user_2)

        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)

    def setUp(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=FollowCreateTest.author)

    def test_correct_follow_work(self):
        """Проверка подписки на автора."""
        FollowCreateTest.auth_client_1.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertTrue(
            Follow.objects.filter(user=FollowCreateTest.user_1,
                                  author=FollowCreateTest.author).exists(),
            'Ошибка подписки на автора'
        )

    def test_correct_unfollow_work(self):
        """Проверка отписки от автора."""
        FollowCreateTest.auth_client_1.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertFalse(
            Follow.objects.filter(user=FollowCreateTest.user_1,
                                  author=FollowCreateTest.author).exists(),
            'Ошибка отписки от автора'
        )

    def test_exist_post_in_page_followers(self):
        """
        Проверка появления записи у подписчиков
        и отсутствия ее у остальных пользователей.
        """
        FollowCreateTest.auth_client_1.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        response_client_1 = FollowCreateTest.auth_client_1.get(
            reverse('posts:follow_index')
        )
        response_client_2 = FollowCreateTest.auth_client_2.get(
            reverse('posts:follow_index')
        )

        self.assertIn(self.post,
                      response_client_1.context['page_obj'],
                      'Новый пост должен находиться в листе подписок')

        self.assertNotIn(self.post,
                         response_client_2.context['page_obj'],
                         'Ошибочное размещение записи')


class PaginatorViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='auth_user')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )

        posts_list = []

        for i in range(COUNT_POSTS):
            posts_list.append(
                Post(text=f'Тестовый текст поста {i}',
                     author=self.user,
                     group=self.group)
            )

        Post.objects.bulk_create(posts_list)

        cache.clear()

    def test_correct_work_paginator(self):
        """Проверка корректной работы паджинатора."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user})
        ]

        for name in reverse_names:
            response = self.auth_client.get(name)

            self.assertEqual(len(response.context['page_obj']),
                             settings.POSTS_ON_PAGE,
                             ('Количество записей на странице'
                              f' должно быть = {settings.POSTS_ON_PAGE}'))

            response = self.auth_client.get(
                name + f'?page={NUMBER_LAST_PAGE}')

            self.assertEqual(len(response.context['page_obj']),
                             POSTS_ON_LAST_PAGE,
                             ('Количество записей на последней странице'
                              f' должно быть = {POSTS_ON_LAST_PAGE}'))
