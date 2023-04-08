from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверка корректности работы __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_names = {
            post: f'{post.text[:15]} ...',
            group: group.title,
        }
        for field, expected_value in expected_object_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    str(field),
                    expected_value,
                    f'Вывод {field} не соответствует {expected_value}'
                )

    def test_verbose_name(self):
        """Проверка verbose_name."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value,
                    f'Поле {field} ожидает значение {expected_value}'
                )

    def test_help_text(self):
        """Проверка help_text."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Здесь вы можете поделиться своими мыслями',
            'group': 'Выберите группу для своей записи'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value,
                    f'Поле {field} ожидает значение {expected_value}'
                )
