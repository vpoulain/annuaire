#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from tldextract import extract

from vote.managers import VotableManager
from s3direct.fields import S3DirectField
from autoslug import AutoSlugField

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Count


class UserProfile(User):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture_url = models.URLField()


class CategoryManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class Category(models.Model):

    objects = CategoryManager()

    class Meta:
        verbose_name_plural = "categories"

    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):

    name = models.CharField(max_length=25, unique=True)
    category = models.ForeignKey(Category, related_name='sub_categories')

    def __str__(self):
        return '<{}> : {}'.format(self.category.name,
                                  self.name)

    class Meta:
        verbose_name_plural = "sub_categories"


class Project(models.Model):

    title = models.CharField(max_length=50, unique=True)
    slug = AutoSlugField(populate_from='title')
    slogan = models.CharField(max_length=250)
    description = models.TextField(max_length=1500)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    url = models.URLField(unique=True)
    image = S3DirectField(dest='imgs', blank=True, help_text='Le ratio de l\'image sera conservé. Préférez un format carré')
    released_date = models.DateTimeField(null=True, blank=True)
    draft = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    youtube_identifier = models.CharField(blank=True, max_length=20, help_text='Fournir l\'identifiant youtube situé après "v=" dans l\'URL par exemple "2xegsh1CmPU" dans "https://www.youtube.com/watch?v=2xegsh1CmPU"')
    vimeo_identifier = models.CharField(blank=True, max_length=20, help_text='Fournir l\'identifiant videmo situé, par exemple "112137027" dans "https://vimeo.com/112137027". Attention la vidéo Youtube est affichée prioritairement si deux identifiants sont fournit.')
    twitter_url = models.CharField(max_length=50, blank=True)
    facebook_url = models.CharField(max_length=50, blank=True)
    categories = models.ManyToManyField(Category, related_name='projects')
    sub_categories = models.ManyToManyField(SubCategory,
                                            related_name='projects',
                                            help_text='Le mieux est de sélectionner une sous catégorie appartenant à un catégorie du projet ;)',
                                            blank=True)
    contact_name = models.CharField(max_length=250, blank=True)
    contact_telephone = models.CharField(max_length=20, blank=True)
    contact_mail = models.EmailField(blank=True)
    blog_article_url = models.URLField(blank=True)
    votes = VotableManager()

    def __str__(self):
        return self.title.capitalize()

    def clean_url(self):
        return '{uri.domain}.{uri.suffix}'.format(uri=extract(self.url))

    @classmethod
    def search(cls, query):
        q_title = Q(title__icontains=query)
        q_slogan = Q(slogan__icontains=query)
        q_description = Q(description__icontains=query)
        q_category = Q(categories__name__icontains=query)
        q_sub_category = Q(sub_categories__name__icontains=query)

        return Project.objects.filter(q_title | q_slogan | q_category | q_sub_category | q_description).annotate(score=Count('votes')).order_by('score').distinct().all()
