from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.dream_brain_data, name='dream_brain_data'),
]
