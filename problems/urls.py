from django.urls import path
from . import views

urlpatterns = [
    path('', views.topics_list, name='topics'),  
    path('topics/<int:topic_id>/', views.topic_problems, name='topic_problems'),
    path('problem/<int:pk>/', views.problem_detail, name='problem_detail'),
]
