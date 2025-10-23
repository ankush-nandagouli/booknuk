from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("librarians/manage/", views.librarians_dashboard, name="librarians_dashboard"),
    path("librarians/add/", views.add_librarian, name="add_librarian"),
    path("librarians/<slug:slug>/edit/", views.edit_librarian, name="edit_librarian"),
    path("librarians/<slug:slug>/delete/", views.delete_librarian, name="delete_librarian"),
    path("librarians/<slug:slug>/toggle-status/", views.toggle_librarian_status, name="toggle_librarian_status"),
]
