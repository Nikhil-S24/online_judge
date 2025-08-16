from django.urls import path
from compiler.views import compile_code, submit_code, view_all_submissions, submission_detail, run_code

urlpatterns = [
    path('run/', run_code, name='run_code'),
    path('compile/', compile_code, name='compile_code'),      
    path('submit/', submit_code, name='submit_code'),         
    path('my-submissions/', view_all_submissions, name='my_submissions'),
    path('submission/<int:pk>/', submission_detail, name='submission_detail'),
]