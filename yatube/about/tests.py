from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus

User = get_user_model()


class AboutURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

    def test_URL_address_available(self):
        """Проверка доступности URL-адресов."""
        url_status = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK
        }

        for url_address, status in url_status.items():
            with self.subTest(url_address=url_address):
                response = AboutURLTests.guest_client.get(url_address)
                self.assertEqual(
                    response.status_code,
                    status,
                    (f'Статус запроса страницы {url_address}'
                     f' не соответствует {status}')
                )

    def test_URL_uses_correct_templates(self):
        """Проверка соответствия URL-адресов и шаблонов."""
        url_address_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }

        for url_address, template in url_address_template.items():
            with self.subTest(url_address=url_address):
                response = AboutURLTests.guest_client.get(url_address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'URL {url_address} ожидает шаблон {template}'
                )
