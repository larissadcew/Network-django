from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Profile, Post

User = get_user_model()

class ModelsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.user3 = User.objects.create_user(username='user3', password='pass3')

        # Crie perfis para os usuários
        self.profile1 = Profile.objects.create(user=self.user1)
        self.profile2 = Profile.objects.create(user=self.user2)
        self.profile3 = Profile.objects.create(user=self.user3)

        # Crie um post para testar os métodos relacionados a posts
        self.post = Post.objects.create(user=self.user1, post='Post de teste')

    def test_like_post_count(self):
        """Testa se o like_count retorna o número correto de likes."""
        self.post.like_post(self.user2)
        self.post.like_post(self.user3)
        self.assertEqual(self.post.like_count(), 2)

    def test_like_own_post(self):
        """Testa que um usuário pode curtir o próprio post."""
        result = self.post.like_post(self.user1)
        self.assertTrue(result)
        self.assertEqual(self.post.like_count(), 1)

    def test_like_post_twice(self):
        """Testa que um usuário não pode curtir o mesmo post duas vezes."""
        result1 = self.post.like_post(self.user2)
        result2 = self.post.like_post(self.user2)
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertEqual(self.post.like_count(), 1)

    def test_unlike_post_not_liked(self):
        """Testa que não é possível descurtir um post que não foi curtido."""
        result = self.post.unlike_post(self.user2)
        self.assertFalse(result)
        self.assertEqual(self.post.like_count(), 0)

    def test_is_following(self):
        """Testa o método is_following do perfil."""
        self.profile1.follow(self.user2)
        self.assertTrue(self.profile1.is_following(self.user2))
        self.assertFalse(self.profile2.is_following(self.user1))

    def test_follower_and_following_count(self):
        """Testa os métodos follower_count e following_count."""
        self.profile1.follow(self.user2)
        self.profile1.follow(self.user3)
        self.profile2.follow(self.user1)

        self.assertEqual(self.profile1.following_count(), 2)
        self.assertEqual(self.profile1.follower_count(), 1)

        self.assertEqual(self.profile2.following_count(), 1)
        self.assertEqual(self.profile2.follower_count(), 1)

        self.assertEqual(self.profile3.following_count(), 0)
        self.assertEqual(self.profile3.follower_count(), 1)

    def test_follow_already_following(self):
        """Testa que não é possível seguir um usuário que já está sendo seguido."""
        result1 = self.profile1.follow(self.user2)
        result2 = self.profile1.follow(self.user2)
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertEqual(self.profile1.following_count(), 1)

    def test_unfollow_not_following(self):
        """Testa que não é possível deixar de seguir um usuário que não está sendo seguido."""
        result = self.profile1.unfollow(self.user2)
        self.assertFalse(result)
        self.assertEqual(self.profile1.following_count(), 0)

    def test_unfollow_user(self):
        """Testa deixar de seguir um usuário."""
        self.profile1.follow(self.user2)
        result = self.profile1.unfollow(self.user2)
        self.assertTrue(result)
        self.assertFalse(self.profile1.is_following(self.user2))
        self.assertEqual(self.profile1.following_count(), 0)
        self.assertEqual(self.profile2.follower_count(), 0)

    def test_follow_self(self):
        """Testa que um usuário não pode seguir a si mesmo."""
        with self.assertRaises(ValidationError):
            self.profile1.follow(self.user1)

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')

        # Autentica o cliente
        self.client.login(username='testuser', password='pass123')

        # Cria 3 posts para testar
        self.posts = [
            Post.objects.create(user=self.user, post=f'Post número {i+1}') for i in range(3)
        ]

    def test_index(self):
        """
        Testa a view da página inicial para garantir que retorna status 200 e contém 3 posts.
        """
        response = self.client.get(reverse('allposts'))  # Ajuste conforme seu namespace
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 3)
        for post in self.posts:
            self.assertContains(response, post.post)