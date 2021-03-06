from json import dumps

from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Count

from .forms import SubmissionForm, ContactForm

from .models import Project, Category, SubCategory


class ProjectIndexView(ListView):
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('search')
        category = self.request.GET.get('category')
        sub_cats = self.request.GET.get('sub_cat')
        # as_list = self.request.GET.get('as_list')

        if query:
            projects_list = Project.search(query)
        elif category and not sub_cats:
            projects_list = Category.objects.order_by('name').get(name=category)\
                .projects.annotate(score=Count('votes')).order_by('-featured', '-score').all()
        elif category and sub_cats:
            projects_list = Category.objects.get(name=category)\
                .projects.annotate(score=Count('votes')).order_by('-featured', '-score').filter(sub_categories__pk__in=sub_cats.split(',')).distinct()
        else:
            projects_list = Project.objects.annotate(score=Count('votes')).order_by('-featured', '-score').all()

        if not self.request.user.is_staff:
            projects_list = projects_list.filter(draft=False)

        return projects_list

    def get_context_data(self, **kwargs):
        context = super(ProjectIndexView, self).get_context_data(**kwargs)
        category_name = self.request.GET.get('category')
        selected_sub_cats = self.request.GET.get('sub_cat')

        if category_name:
            category = Category.objects.get(name=category_name)
            context['category'] = category
            context['sub_categories'] = category\
                .sub_categories.all()

        if selected_sub_cats:
            context['selected_sub_categories'] = SubCategory.objects.filter(pk__in=selected_sub_cats.split(','))

        user = self.request.user
        if user.is_authenticated():
            context['liked_projects'] = Project.votes.all(user)
        else:
            context['liked_projects'] = []

        return context


class ProjectDetailView(DetailView):

    model = Project
    context_object_name = 'project'

    query_pk_and_slug = True

    def get_queryset(self, *args, **kwargs):
        queryset = super(ProjectDetailView, self).get_queryset(*args, **kwargs
            )
        if not self.request.user.is_staff:
            return queryset.filter(draft=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated():
            context['liked_projects'] = Project.votes.all(user)
        else:
            context['liked_projects'] = []
        return context


DEFAULT_FROM_EMAIL = 'contact@consocollaborative.com'

MANAGERS = ['vincent.poulain2@gmail.com',
            'contact@consocollaborative.com',
            'edwin@consocollaborative.com',
            'jeanjacques@consocollaborative.com']


def credits(request):
    return render(request, 'app/credits.html')


def vote(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    user = request.user
    project_id = request.POST['project_id']
    project = Project.objects.get(id=project_id)

    if not project.votes.exists(user):
        project.votes.up(user)
    else:
        project.votes.down(user)

    response = {'count': project.votes.count(),
                'liked': project.votes.exists(user)}
    return HttpResponse(dumps(response), status=201, content_type='application/json')


def submit_project(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            msg_plain = render_to_string('emails/submission.txt', form.cleaned_data)
            msg_html = render_to_string('emails/submission.html', form.cleaned_data)
            send_mail('[Annuaire CC] - Demande d\'ajout de projet : {}'.format(form.cleaned_data['project_name']),
                      msg_plain,
                      DEFAULT_FROM_EMAIL,
                      MANAGERS,
                      html_message=msg_html)
        return render(request, 'app/project_submission_sent.html')
    else:
        form = SubmissionForm()

    return render(request, 'app/project_submission.html', {'form': form})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            msg_plain = render_to_string('emails/contact.txt', form.cleaned_data)
            msg_html = render_to_string('emails/contact.html', form.cleaned_data)
            send_mail('[Annuaire CC] - Formulaire de contact',
                      msg_plain,
                      DEFAULT_FROM_EMAIL,
                      MANAGERS,
                      html_message=msg_html)
        return render(request, 'app/contact.html')
    else:
        form = ContactForm()

    return render(request, 'app/contact.html', {'form': form})
