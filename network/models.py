from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    def get_profile(self):
        """Retorna o perfil associado ao usuário."""
        return self.profile

    def __str__(self):
        return self.username


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post = models.CharField(max_length=500, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    like = models.ManyToManyField(User, blank=True, related_name="liked_posts")

    def __str__(self):
        return f"{self.user.username}: {self.post[:20]}..."

    def like_post(self, user):
        """Adiciona um like ao post por um usuário."""
        if not self.like.filter(id=user.id).exists():
            self.like.add(user)
            return True
        return False

    def unlike_post(self, user):
        """Remove um like do post por um usuário."""
        if self.like.filter(id=user.id).exists():
            self.like.remove(user)
            return True
        return False

    def like_count(self):
        """Retorna o número de likes no post."""
        return self.like.count()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    follower = models.ManyToManyField(User, blank=True, related_name="followers")
    following = models.ManyToManyField(User, blank=True, related_name="followings")

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def follow(self, user):
        """Faz o usuário seguir outro usuário."""
        if user == self.user:
            raise ValidationError("Usuário não pode seguir a si mesmo.")
        if not self.following.filter(id=user.id).exists():
            self.following.add(user)
            user.profile.follower.add(self.user)
            return True
        return False

    def unfollow(self, user):
        """Faz o usuário deixar de seguir outro usuário."""
        if self.following.filter(id=user.id).exists():
            self.following.remove(user)
            user.profile.follower.remove(self.user)
            return True
        return False

    def is_following(self, user):
        """Verifica se o usuário está seguindo outro usuário."""
        return self.following.filter(id=user.id).exists()

    def follower_count(self):
        """Retorna o número de seguidores."""
        return self.follower.count()

    def following_count(self):
        """Retorna o número de usuários que está seguindo."""
        return self.following.count()