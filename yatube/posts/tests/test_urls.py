from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus
from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='auth_user')
        cls.author = User.objects.create_user(username='author')

        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)

    def setUp(self):
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        self.post = Post.objects.create(
            text='Тестовый текст поста',
            author=PostURLTests.author,
            group=self.group
        )

    def test_url_address_available(self):
        """Проверка доступности URL-адресов для разных пользователей."""
        users_urls_status = {
            PostURLTests.guest_client:
            (['/', HTTPStatus.OK],
             [f'/group/{self.group.slug}/', HTTPStatus.OK],
             [f'/profile/{self.post.author}/', HTTPStatus.OK],
             [f'/posts/{self.post.id}/', HTTPStatus.OK],
             ['/create/', HTTPStatus.FOUND],
             [f'/posts/{self.post.id}/edit/', HTTPStatus.FOUND],
             [f'/posts/{self.post.id}/comment/', HTTPStatus.FOUND],
             [f'/posts/{self.post.id}/delete/', HTTPStatus.FOUND],
             ['/unexisting_page/', HTTPStatus.NOT_FOUND],),
            PostURLTests.auth_client:
            (['/create/', HTTPStatus.OK],
             [f'/posts/{self.post.id}/edit/', HTTPStatus.FOUND],
             [f'/posts/{self.post.id}/delete/', HTTPStatus.FOUND],),
            PostURLTests.auth_client_author:
            ([f'/posts/{self.post.id}/edit/', HTTPStatus.OK],
             [f'/posts/{self.post.id}/delete/', HTTPStatus.FOUND],)
        }

        for client, url_response in users_urls_status.items():
            with self.subTest(client=client):
                for i in range(len(url_response)):
                    response = client.get(url_response[i][0])
                    self.assertEqual(
                        response.status_code,
                        url_response[i][1],
                        (f'Статус запроса страницы {url_response[i][0]}'
                         ' не соответствует ожидаемому')
                    )

    def test_correct_redirect(self):
        """
        Проверка корректности редиректа
        для авторизованного и неавторизованного пользователей.
        """
        urls_redirect = [
            '/create/',
            f'/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/',
            f'/posts/{self.post.id}/delete/',
        ]

        for url in urls_redirect:
            response = PostURLTests.guest_client.get(url, follow=True)
            self.assertRedirects(response, f'/auth/login/?next={url}')

        for url in urls_redirect[1:]:
            response = PostURLTests.auth_client.get(url, follow=True)
            self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_URL_uses_correct_templates(self):
        """Проверка соответствия URL-адресов и шаблонов."""
        url_address_template = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            '/unexisting_page/': 'core/404.html',
        }

        for url_address, template in url_address_template.items():
            with self.subTest(url_address=url_address):
                response = PostURLTests.auth_client_author.get(url_address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'URL {url_address} ожидает шаблон {template}'
                )
