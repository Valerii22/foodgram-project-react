from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    username = models.CharField(
        verbose_name='Логин',
        max_length=150,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким никнеймом уже существует!',
        },
        help_text='Укажите свой никнейм'
    )
    first_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='First Name',
    )
    last_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Last Name',
    )
    email = models.EmailField(
        'email address',
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscribe'
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following'
            )
        ]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'