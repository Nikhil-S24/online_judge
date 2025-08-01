from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'verdict', 'submitted_at')  # fixed
    search_fields = ('user__username', 'problem__title', 'verdict')
    list_filter = ('language', 'verdict', 'submitted_at') 
