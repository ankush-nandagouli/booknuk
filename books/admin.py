from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'available', 'uploaded_at')
    search_fields = ('title', 'author', 'category')
    list_filter = ('category', 'available')
    prepopulated_fields = {'slug': ('title',)}
