from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Post, Profile

User = get_user_model()

class ModelsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.post = Post.objects.create(user=self.user1, post='Este é um post de teste.')

    def test_like_post(self):
        # User2 gosta do post de User1
        result = self.post.like_post(self.user2)
        self.assertTrue(result)
        self.assertEqual(self.post.like_count(), 1)
        # User2 tenta curtir novamente
        result = self.post.like_post(self.user2)
        self.assertFalse(result)
        self.assertEqual(self.post.like_count(), 1)

    def test_unlike_post(self):
        self.post.like_post(self.user2)
        result = self.post.unlike_post(self.user2)
        self.assertTrue(result)
        self.assertEqual(self.post.like_count(), 0)
        # User2 tenta descurtir novamente
        result = self.post.unlike_post(self.user2)
        self.assertFalse(result)

    def test_follow_user(self):
        profile1 = self.user1.get_profile()
        result = profile1.follow(self.user2)
        self.assertTrue(result)
        self.assertTrue(profile1.is_following(self.user2))
        self.assertEqual(self.user2.profile.follower_count(), 1)
        # Tentar seguir novamente
        result = profile1.follow(self.user2)
        self.assertFalse(result)

    def test_unfollow_user(self):
        profile1 = self.user1.get_profile()
        profile1.follow(self.user2)
        result = profile1.unfollow(self.user2)
        self.assertTrue(result)
        self.assertFalse(profile1.is_following(self.user2))
        self.assertEqual(self.user2.profile.follower_count(), 0)
        # Tentar deixar de seguir novamente
        result = profile1.unfollow(self.user2)
        self.assertFalse(result)

    def test_follow_self(self):
        profile1 = self.user1.get_profile()
        with self.assertRaises(ValidationError):
            profile1.follow(self.user1)


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Cria 3 posts para testar
        self.posts = [
            Post.objects.create(user=self.user, post=f'Post número {i+1}') for i in range(3)
        ]

    def test_index(self):
        """
        Testa a view da página inicial para garantir que retorna status 200 e contém 3 posts.
        """
        # Faz uma requisição GET para a URL da página inicial usando o nome da URL
        response = self.client.get(reverse('index'))  # Certifique-se de que 'index' é o nome correto da sua URL

        # Verifica se a resposta HTTP tem o status 200
        self.assertEqual(response.status_code, 200)

        # Verifica se o contexto contém 3 posts
        self.assertIn('posts', response.context)  # Verifica se 'posts' está no contexto
        self.assertEqual(len(response.context['posts']), 3)

        # Opcional: Verifica se todos os posts estão presentes na resposta
        for post in self.posts:
            self.assertContains(response, post.post)