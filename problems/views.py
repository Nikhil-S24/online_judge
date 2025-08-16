from django.shortcuts import render, get_object_or_404
from .models import Topic, Problem
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required

@login_required
def topics_list(request):
    topics = Topic.objects.all()
    return render(request, 'problems/topics_list.html', {'topics': topics})

@login_required
def topic_problems(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    problems = Problem.objects.filter(topic=topic)

    search_query = request.GET.get('search', '')
    sort_order = request.GET.get('sort', '')

    if search_query:
        problems = problems.filter(title__icontains=search_query)

    if sort_order == 'title_asc':
        problems = problems.order_by('title')
    elif sort_order == 'title_desc':
        problems = problems.order_by('-title')
    elif sort_order == 'difficulty_asc':
        problems = problems.annotate(
            difficulty_order=Case(
                When(difficulty='Easy', then=Value(1)),
                When(difficulty='Medium', then=Value(2)),
                When(difficulty='Hard', then=Value(3)),
                output_field=IntegerField()
            )
        ).order_by('difficulty_order')
    elif sort_order == 'difficulty_desc':
        problems = problems.annotate(
            difficulty_order=Case(
                When(difficulty='Easy', then=Value(1)),
                When(difficulty='Medium', then=Value(2)),
                When(difficulty='Hard', then=Value(3)),
                output_field=IntegerField()
            )
        ).order_by('-difficulty_order')

    return render(request, 'problems/topic_problems.html', {
        'topic': topic,
        'problems': problems
    })

@login_required
def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    languages = ['Python', 'C++', 'Java', 'JavaScript']

    if request.method == 'POST':
        selected_language = request.POST.get('language')
        user_code = request.POST.get('code')
        return render(request, 'problems/problem_detail.html', {
            'problem': problem,
            'languages': languages,
            'selected_language': selected_language,
            'user_code': user_code,
            'submitted': True
        })

    return render(request, 'problems/problem_detail.html', {
        'problem': problem,
        'languages': languages
    })
