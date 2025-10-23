import datetime
import logging
import random
import requests
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator

from books.models import Book, IssuedBook
from accounts.models import CustomUser
from accounts.forms import LibrarianCreationForm

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()


def home(request):
    year = datetime.datetime.now().year
    thought = "Keep learning, keep growing."

    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                thought = f"{data[0]['q']} — {data[0]['a']}"
    except Exception as e:
        logger.error(f"Quote API Error: {e}")

    # Fetch 3 random books efficiently
    book_count = Book.objects.count()
    if book_count > 0:
        random_indexes = random.sample(range(book_count), min(3, book_count))
        featured_books = [Book.objects.all()[i] for i in random_indexes]
    else:
        featured_books = []

    context = {
        'thought': thought,
        'year': year,
        'featured_books': featured_books,
    }
    return render(request, 'core/home.html', context)


def admin_required(user):
    return user.is_superuser


@user_passes_test(admin_required)
def librarians_dashboard(request):
    librarians_list = CustomUser.objects.filter(role="librarian", is_deleted=False).order_by('username')

    # Pagination for production
    paginator = Paginator(librarians_list, 10)  # 10 librarians per page
    page_number = request.GET.get('page')
    librarians = paginator.get_page(page_number)

    total = librarians_list.count()
    active = librarians_list.filter(is_active=True).count()
    inactive = total - active
    total_books = Book.objects.count()
    total_books_issued = IssuedBook.objects.count()

    context = {
        "librarians": librarians,
        "total": total,
        "active": active,
        "inactive": inactive,
        "total_books": total_books,
        "total_books_issued": total_books_issued,
        "paginator": paginator,
    }
    return render(request, "core/librarians_dashboard.html", context)


@user_passes_test(admin_required)
def add_librarian(request):
    if request.method == "POST":
        form = LibrarianCreationForm(request.POST)
        if form.is_valid():
            librarian = form.save(commit=False)
            librarian.role = "librarian"
            librarian.save()
            messages.success(request, "✅ Librarian added successfully!")
            return redirect("librarians_dashboard")
        else:
            messages.error(request, "⚠️ Please fix the errors below.")
    else:
        form = LibrarianCreationForm()
    return render(request, "core/add_librarian.html", {"form": form})


@user_passes_test(admin_required)
def edit_librarian(request, slug):
    librarian = get_object_or_404(CustomUser, slug=slug, role="librarian", is_deleted=False)
    if request.method == "POST":
        form = LibrarianCreationForm(request.POST, instance=librarian)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Librarian updated successfully!")
            return redirect("librarians_dashboard")
        else:
            messages.error(request, "⚠️ Please fix the errors below.")
    else:
        form = LibrarianCreationForm(instance=librarian)
    return render(request, "core/edit_librarian.html", {"form": form})


@user_passes_test(admin_required)
def delete_librarian(request, slug):
    librarian = get_object_or_404(CustomUser, slug=slug, role="librarian", is_deleted=False)
    # Soft delete instead of hard delete
    librarian.is_deleted = True
    librarian.is_active = False
    librarian.save()
    messages.success(request, "🗑️ Librarian deleted successfully!")
    logger.info(f"Librarian {librarian.username} soft deleted by {request.user.username}")
    return redirect("librarians_dashboard")


@user_passes_test(admin_required)
def toggle_librarian_status(request, slug):
    librarian = get_object_or_404(CustomUser, slug=slug, role="librarian", is_deleted=False)
    librarian.is_active = not librarian.is_active
    librarian.save()
    status = "activated" if librarian.is_active else "suspended"
    messages.success(request, f"⚡ Librarian {status} successfully!")
    logger.info(f"Librarian {librarian.username} {status} by {request.user.username}")
    return redirect("librarians_dashboard")
