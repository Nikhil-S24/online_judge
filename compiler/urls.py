from django.urls import path
from . import views
from .views import compile_code, submission_history, submission_detail

urlpatterns = [
    path('compile/', compile_code, name='compile_code'),
    path('submission-history/<int:problem_id>/', views.submission_history, name='submission_history'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
]
