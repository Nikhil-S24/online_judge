from django.contrib import admin
from django.urls import path, include
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('', views.home, name='home'),  # Home page
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('accounts/login/', views.custom_login),

    path('problems/', include('problems.urls')),
    path('compiler/', include('compiler.urls')),
]
