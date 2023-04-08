from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm
from utils.paginator import get_paginator


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group').all()
    page_obj = get_paginator(request, posts)
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    page_obj = get_paginator(request, posts)
    context = {
        'title': f'Записи сообщества {group}',
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def groups_info(request):
    template = 'posts/groups_info.html'
    groups = Group.objects.all()
    context = {
        'title': 'Все группы',
        'groups': groups,
    }
    return render(request, template, context)


def authors_info(request):
    template = 'posts/authors_info.html'
    all_authors = User.objects.all()
    context = {
        'title': 'Все авторы',
        'all_authors': all_authors,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    my_followings = User.objects.filter(following__user=author)
    my_followers = User.objects.filter(follower__author=author)
    posts = author.posts.select_related('author', 'group').all()
    page_obj = get_paginator(request, posts)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context = {
        'author': author,
        'my_followings': my_followings,
        'my_followers': my_followers,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post_choice = get_object_or_404(Post, pk=post_id)
    comments = post_choice.comments.all()
    form = CommentForm()
    context = {
        'post_choice': post_choice,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request,
                  template,
                  {'form': form, 'post': post, 'is_edit': True})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.select_related('author').filter(
        author__following__user=request.user
    )
    page_obj = get_paginator(request, posts)
    context = {
        'title': 'Мои подписки',
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(user=request.user,
                          author__username=username).delete()
    return redirect("posts:profile", username=username)
