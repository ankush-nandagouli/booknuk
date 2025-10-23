from django.urls import path
from . import views
app_name = "faculty"
urlpatterns = [
    path('send-notification/', views.send_notifications, name="send_notification"),
    path("students/", views.student_list, name="student_list"),
    path("students/<slug:slug>/profile/", views.students_profile, name="students_profile"),
    path("students/<slug:slug>/suspend/", views.suspend_students, name="suspend_students"),
    path("issue-book/", views.teacher_issue_book, name="teacher_issue_book"),
]
