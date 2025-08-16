from django.contrib import admin
from .models import Topic, Problem,TestCase

# Register your models here.

admin.site.register(Topic)
admin.site.register(Problem)
admin.site.register(TestCase)