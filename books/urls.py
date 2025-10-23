from django.urls import path
from . import views
app_name = "books"
urlpatterns = [
    path('browse/', views.browse_books, name='browse_books'),
    path('add/', views.add_book, name='add_book'),
    #path("bulk-upload/", views.bulk_upload_books, name="bulk_upload_books"),
    path("bulk-add/", views.manual_bulk_add_books, name="manual_bulk_add_books"),
    path("delete-book/", views.delete_books_view, name="delete_books_view"),
    path("confirm-delete/<int:book_id>/", views.delete_book_confirm, name="delete_book_confirm"),
    path('issue/', views.issue_book, name='issue_book'),
    path("issued-books/", views.issued_books_dashboard, name="issued_books_dashboard"),
    path("return-book/<int:issue_id>/", views.return_book, name="return_book"),
    path("my-issued-books/", views.my_issued_books, name="my_issued_books"),
    path('student/<int:student_id>/history/', views.student_book_history, name='student_book_history'),

    path('<slug:slug>/', views.book_detail, name='book_detail'),

]

