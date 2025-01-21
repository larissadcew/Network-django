from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, Post, Profile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.method == "POST":

        # Tenta autenticar o usuário
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Verifica se a autenticação foi bem-sucedida
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("allposts"))
        else:
            # Retorna uma mensagem de erro se as credenciais forem inválidas
            return render(request, "network/login.html", {
                "message": "Nome de usuário e/ou senha inválidos."
            })
    else:
        # Renderiza a página de login para requisições GET
        return render(request, "network/login.html")


@login_required
def logout_view(request):
    # Faz logout do usuário e redireciona para a página de login
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Verifica se a senha corresponde à confirmação
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "As senhas devem corresponder."
            })

        # Tenta criar um novo usuário
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            # Retorna uma mensagem de erro se o nome de usuário já estiver em uso
            return render(request, "network/register.html", {
                "message": "Nome de usuário já está em uso."
            })
        # Faz login do usuário recém-criado
        login(request, user)
        # Cria um perfil para o novo usuário
        profile = Profile()
        profile.user = user
        profile.save()
        return HttpResponseRedirect(reverse("allposts"))
    else:
        # Renderiza a página de registro para requisições GET
        return render(request, "network/register.html")


@login_required
def allPost(request):
    # Obtém todos os posts ordenados pelo timestamp mais recente
    posts = Post.objects.all().order_by('-timestamp')
    paginator = Paginator(posts, 10)  # Pagina os posts, 10 por página
    if request.GET.get("page") != None:
        try:
            posts = paginator.page(request.GET.get("page"))
        except:
            # Se a página solicitada não for válida, retorna a página 1
            posts = paginator.page(1)
    else:
        # Se nenhuma página for especificada, retorna a primeira página
        posts = paginator.page(1)
    # Renderiza a página de todos os posts
    return render(request, 'network/allpost.html', {'posts': posts})


@login_required
def profile(request, username):
    try:
        # Obtém o usuário e seu perfil com base no nome de usuário
        user = User.objects.get(username=username)
        profile = Profile.objects.get(user=user)
        users_profile = Profile.objects.get(user=request.user)
    except:
        # Retorna uma página de erro se o usuário não for encontrado
        return render(request, 'network/profile.html', {"error": True})
    # Obtém os posts do usuário específico
    posts = Post.objects.filter(user=user).order_by('-timestamp')
    paginator = Paginator(posts, 10)  # Pagina os posts, 10 por página
    if request.GET.get("page") != None:
        try:
            posts = paginator.page(request.GET.get("page"))
        except:
            posts = paginator.page(1)
    else:
        posts = paginator.page(1)
    # Debug: imprime os seguidores do perfil do usuário atual no console
    for i in users_profile.follower.all():
        print(i)
    context = {
        'posts': posts,
        "user": user,
        "profile": profile,
        'users_profile': users_profile
    }
    # Renderiza a página de perfil com o contexto fornecido
    return render(request, 'network/profile.html', context)


@login_required
def following(request):
    # Obtém a lista de usuários que o usuário atual está seguindo
    following = Profile.objects.get(user=request.user).following.all()
    # Obtém os posts dos usuários seguidos, ordenados pelo timestamp mais recente
    posts = Post.objects.filter(user__in=following).order_by('-timestamp')
    paginator = Paginator(posts, 10)  # Pagina os posts, 10 por página
    if request.GET.get("page") != None:
        try:
            posts = paginator.page(request.GET.get("page"))
        except:
            posts = paginator.page(1)
    else:
        posts = paginator.page(1)
    # Renderiza a página de posts seguidos
    return render(request, 'network/following.html', {'posts': posts})


@login_required
@csrf_exempt
def like(request):
    if request.method == "POST":
        post_id = request.POST.get('id')  # Obtém o ID do post a ser curtido/descurtido
        is_liked = request.POST.get('is_liked')  # Estado atual do like

        try:
            post = Post.objects.get(id=post_id)
            if is_liked == 'no':
                # Adiciona o usuário aos likes do post
                post.like.add(request.user)
                is_liked = 'yes'
            elif is_liked == 'yes':
                # Remove o usuário dos likes do post
                post.like.remove(request.user)
                is_liked = 'no'
            post.save()

            # Retorna a contagem atualizada de likes e o novo estado
            return JsonResponse({'like_count': post.like.count(), 'is_liked': is_liked, "status": 201})
        except:
            # Retorna um erro se o post não for encontrado
            return JsonResponse({'error': "Post não encontrado", "status": 404})
    # Retorna um erro para métodos que não sejam POST
    return JsonResponse({}, status=400)


@login_required
@csrf_exempt
def follow(request):
    if request.method == "POST":
        user = request.POST.get('user')  # Nome de usuário a ser seguido/seguido
        action = request.POST.get('action')  # Ação: 'Follow' ou 'Unfollow'

        if action == 'Follow':
            try:
                # Obtém o usuário a ser seguido
                user = User.objects.get(username=user)
                profile = Profile.objects.get(user=request.user)
                profile.following.add(user)  # Adiciona o usuário à lista de seguindo
                profile.save()

                # Adiciona o usuário atual à lista de seguidores do usuário seguido
                profile = Profile.objects.get(user=user)
                profile.follower.add(request.user)
                profile.save()
                # Retorna o novo estado da ação e a contagem de seguidores
                return JsonResponse({'status': 201, 'action': "Unfollow", "follower_count": profile.follower.count()}, status=201)
            except:
                # Retorna um erro se o usuário não for encontrado
                return JsonResponse({}, status=404)
        else:
            try:
                # Obtém o usuário a ser deixado de seguir
                user = User.objects.get(username=user)
                profile = Profile.objects.get(user=request.user)
                profile.following.remove(user)  # Remove o usuário da lista de seguindo
                profile.save()

                # Remove o usuário atual da lista de seguidores do usuário deixado de seguir
                profile = Profile.objects.get(user=user)
                profile.follower.remove(request.user)
                profile.save()
                # Retorna o novo estado da ação e a contagem de seguidores
                return JsonResponse({'status': 201, 'action': "Follow", "follower_count": profile.follower.count()}, status=201)
            except:
                # Retorna um erro se o usuário não for encontrado
                return JsonResponse({}, status=404)

    # Retorna um erro para métodos que não sejam POST
    return JsonResponse({}, status=400)


@login_required
@csrf_exempt
def edit_post(request):
    if request.method == "POST":
        post_id = request.POST.get('id')  # Obtém o ID do post a ser editado
        new_post = request.POST.get('post')  # Novo conteúdo do post
        try:
            post = Post.objects.get(id=post_id)
            if post.user == request.user:
                # Atualiza o conteúdo do post e salva
                post.post = new_post.strip()
                post.save()
                return JsonResponse({}, status=201)
        except:
            # Retorna um erro se o post não for encontrado
            return JsonResponse({}, status=404)

    # Retorna um erro para métodos que não sejam POST
    return JsonResponse({}, status=400)


@login_required
@csrf_exempt
def addpost(request):
    if request.method == "POST":
        post = request.POST.get('post')  # Conteúdo do novo post
        if len(post) != 0:
            obj = Post()
            obj.post = post
            obj.user = request.user
            obj.save()
            context = {
                'status': 201,
                'post_id': obj.id,
                'username': request.user.username,
                'timestamp': obj.timestamp.strftime("%B %d, %Y, %I:%M %p"),
            }
            # Retorna os detalhes do novo post criado
            return JsonResponse(context, status=201)
    # Retorna um erro se o post estiver vazio ou método não for POST
    return JsonResponse({}, status=400)