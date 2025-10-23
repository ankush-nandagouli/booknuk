from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # import all views as a module

urlpatterns = [
    # -------------------
    # General User
    # -------------------
    path('register/', views.register, name='register'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/teacher/', views.teacher_register, name='teacher_register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('student-profile/<int:user_id>/', views.student_profile_view, name='student_profile'),

    # -------------------
    # Librarian
    # -------------------
    path('librarian/login/', views.librarian_login, name='librarian_login'),
    path('librarian/profile/', views.librarian_profile, name='librarian_profile'),
    path('librarian/profile-update/', views.librarian_profile_update, name='librarian_profile_update'),
    path('librarian/dashboard/', views.librarian_dashboard, name='librarian_dashboard'),
    path('librarian/pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('librarian/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('librarian/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('librarian/export/', views.export_users_csv, name='export_users_csv'),
    path('librarian/registered-students/', views.registered_students, name='registered_students'),
    path('librarian/registered-teachers/', views.registered_teachers, name='registered_teachers'),
    path('librarian/students/', views.student_management, name='student_management'),
    path('librarian/students/<int:student_id>/', views.view_student_profile, name='view_student_profile'),
    path('librarian/students/<int:student_id>/toggle-suspend/', views.toggle_suspend_student, name='toggle_suspend_student'),

    # -------------------
    # Teacher
    # -------------------
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/suspend/<int:user_id>/', views.suspend_student, name='suspend_student'),

    # -------------------
    # Password Reset
    # -------------------
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
