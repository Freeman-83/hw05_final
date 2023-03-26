from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Имя группы', max_length=200)
    slug = models.SlugField('URL', unique=True)
    description = models.TextField('Описание')

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Здесь вы можете поделиться своими мыслями',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу для своей записи',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Выберите картинку для своей записи'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self) -> str:
        return f'{self.text[:15]} ...'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        'Добавить комментарий',
        help_text='Будьте взаимовежливы',
    )
    created = models.DateTimeField(
        'Дата публикации комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return f'{self.text[:15]} ...'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
