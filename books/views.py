from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookForm, ManualBulkBookFormSet, IssueBookForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Book, IssuedBook
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
#import csv, io, zipfile, os
#from django.core.files.base import ContentFile
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from django.utils.timezone import now
from .models import CustomUser
from django.http import HttpResponse
import csv

def browse_books(request):
    books = Book.objects.filter(available=True).order_by('-uploaded_at')  # Filter only available books

    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if category_filter:
        books = books.filter(category=category_filter)

    paginator = Paginator(books, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Book.CATEGORY_CHOICES

    return render(request, 'books/browse_books.html', {
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'categories': categories
    })


def is_librarian(user):
    return user.is_authenticated and user.is_librarian

@login_required
@user_passes_test(is_librarian)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            if book.available is None:
                book.available = True  # fallback safety
            book.save()
            messages.success(request, "✅ Book added successfully!")
            return redirect('books:browse_books')
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})

@login_required
def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, 'books/book_detail.html', {'book': book})

'''   
# ---------- CSV + ZIP (covers) bulk upload ----------
@require_http_methods(["GET", "POST"])
def bulk_upload_books(request):
    """
    Upload CSV + ZIP:
      - CSV columns: title,author,isbn,total_copies,available_copies,description,category (category optional)
      - ZIP: images named <isbn>.jpg/.jpeg/.png
      - PDF is NOT supported here (manual later).
    """
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        zip_file = request.FILES.get("cover_zip")

        if not csv_file:
            messages.error(request, "Please upload the CSV file.")
            return redirect("books:bulk_upload_books")
        if not zip_file:
            messages.error(request, "Please upload the Cover ZIP file.")
            return redirect("books:bulk_upload_books")

        # Build map {isbn: bytes}
        covers = {}
        try:
            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    base = os.path.basename(name)
                    if not base:
                        continue
                    root, ext = os.path.splitext(base)
                    if ext.lower() in [".jpg", ".jpeg", ".png"]:
                        covers[root.strip()] = zf.read(name)
        except zipfile.BadZipFile:
            messages.error(request, "The cover file is not a valid ZIP.")
            return redirect("books:bulk_upload_books")

        # Parse CSV
        created, updated, skipped = 0, 0, 0
        warnings = []

        try:
            text = csv_file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
        except Exception as e:
            messages.error(request, f"Could not read CSV: {e}")
            return redirect("books:bulk_upload_books")

        # Bulk operation
        with transaction.atomic():
            for idx, row in enumerate(reader, start=2):  # header = row 1
                try:
                    isbn = (row.get("isbn") or "").strip()
                    if not isbn:
                        skipped += 1
                        warnings.append(f"Row {idx}: missing ISBN → skipped.")
                        continue

                    defaults = {
                        "title": (row.get("title") or "").strip(),
                        "author": (row.get("author") or "").strip(),
                        "category": (row.get("category") or "").strip(),
                        "description": (row.get("description") or "").strip(),
                        "total_copies": int(row.get("total_copies") or 0),
                        "available_copies": int(row.get("available_copies") or 0),
                    }
                    # Validate stock
                    if defaults["available_copies"] > defaults["total_copies"]:
                        skipped += 1
                        warnings.append(f"Row {idx} (ISBN {isbn}): available_copies > total_copies → skipped.")
                        continue

                    # Create or update by ISBN
                    book, created_flag = Book.objects.update_or_create(
                        isbn=isbn,
                        defaults=defaults
                    )

                    # Attach cover if present
                    img_bytes = covers.get(isbn)
                    if img_bytes:
                        # Guess jpg if not sure; name will set upload path
                        book.cover_image.save(f"{isbn}.jpg", ContentFile(img_bytes), save=True)

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                except IntegrityError as e:
                    skipped += 1
                    warnings.append(f"Row {idx} (ISBN {row.get('isbn')}): DB integrity error → {e}")
                except Exception as e:
                    skipped += 1
                    warnings.append(f"Row {idx} (ISBN {row.get('isbn')}): {e}")

        # Messages
        if created or updated:
            messages.success(request, f"Upload complete: {created} created, {updated} updated, {skipped} skipped.")
        if warnings:
            for w in warnings[:8]:  # don’t flood UI
                messages.warning(request, w)
            if len(warnings) > 8:
                messages.warning(request, f"...and {len(warnings) - 8} more warnings.")

        return redirect("books:bulk_upload_books")

    return render(request, "books/bulk_upload_books.html")
'''

# ---------- Manual bulk add via formset ----------
@require_http_methods(["GET", "POST"])
def manual_bulk_add_books(request):
    """
    Add multiple books manually at once (with cover images; PDFs remain manual per book).
    """
    initial_count = int(request.GET.get("rows", 5))
    initial_count = max(1, min(initial_count, 50))  # 1..50 rows

    if request.method == "POST":
        formset = ManualBulkBookFormSet(request.POST, request.FILES, queryset=Book.objects.none())
        if formset.is_valid():
            saved = 0
            with transaction.atomic():
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                        # enforce rule: available ≤ total
                        total = form.cleaned_data.get("total_copies") or 0
                        available = form.cleaned_data.get("available_copies") or 0
                        if available > total:
                            form.add_error("available_copies", "Available copies cannot exceed total copies.")
                            continue
                        form.save()
                        saved += 1
            if saved:
                messages.success(request, f"Saved {saved} book(s).")
                return redirect("books:manual_bulk_add_books")
            else:
                messages.info(request, "Nothing to save. Check your rows.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        formset = ManualBulkBookFormSet(queryset=Book.objects.none())
        formset.extra = initial_count

    return render(request, "books/manual_bulk_add_books.html", {"formset": formset})


@login_required
@user_passes_test(is_librarian)
def delete_books_view(request):
    search_query = request.GET.get("q", "")

    books = Book.objects.all()
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )

    paginator = Paginator(books, 10)  # 10 books per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
    }
    return render(request, "books/delete_books.html", context)


@login_required
@user_passes_test(is_librarian)
def delete_book_confirm(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        book.delete()
        messages.success(request, f"Book '{book.title}' deleted successfully.")
        return redirect("books:delete_books_view")

    return render(request, "books/delete_book_confirm.html", {"book": book})

def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"slug": self.slug})

@user_passes_test(is_librarian)
def issue_book(request):
    if request.method == "POST":
        form = IssueBookForm(request.POST)
        if form.is_valid():
            issued_book = form.save(commit=False)
            # reduce available copies
            issued_book.book.available_copies -= 1
            issued_book.book.save()
            issued_book.issue_date = timezone.now().date()
            issued_book.due_date = timezone.now().date() + timedelta(days=14)
            issued_book.save()
            messages.success(request,f'Book "{issued_book.book.title}" issued successfully to {issued_book.student.get_full_name()}!')
            return redirect('librarian_dashboard')
    else:
        form = IssueBookForm()
    return render(request, 'books/issue_book.html',{'form': form, 'today': timezone.now().date() , 'due_date': timezone.now() + timedelta(days=14)})

def issued_books_dashboard(request):
    query = request.GET.get("q", "")
    filter_option = request.GET.get("filter", "")

    issues = IssuedBook.objects.all().select_related("student", "book")

    # 🔍 Search by student username, first/last name, or book title
    if query:
        issues = issues.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(book__title__icontains=query)
        )

    # 📌 Apply filters
    if filter_option == "overdue":
        issues = [i for i in issues if not i.return_date and i.due_date.date() < date.today()]

    elif filter_option == "returned":
        issues = issues.filter(return_date__isnull=False)
    elif filter_option == "not_returned":
        issues = issues.filter(return_date__isnull=True)

    context = {
        "issues": issues,
    }
    return render(request, "books/issued_book.html", context)


def return_book(request, issue_id):
    issue = get_object_or_404(IssuedBook, id=issue_id)

    if request.method == "POST":
        if not issue.return_date:
            issue.return_date = now().date()
            issue.book.available_copies += 1
            issue.book.save()
            issue.save()
            messages.success(request, f"Book '{issue.book.title}' returned successfully! Fine: ₹{issue.fine}")
        else:
            messages.warning(request, "This book has already been returned.")
        return redirect("books:issued_books_dashboard")  # redirect to issued books dashboard

    return render(request, "books/return_book.html", {"issue": issue})

@login_required
def my_issued_books(request):
    # Ensure the logged-in user is a student
    if not request.user.is_student():
        messages.error(request, "Only students can view issued books.")
        return render(request, "books/my_issued_books.html", {"issued_books": []})

    student = request.user  # Directly use logged-in student
    issued_books = IssuedBook.objects.filter(student=student, return_date__isnull=True)

    return render(request, "books/my_issued_books.html", {
        "issued_books": issued_books,
        "student": student,
    })

def student_book_history(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    issued_books = IssuedBook.objects.filter(student=student).select_related('book')

    # 🔹 CSV Export
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{student.username}_book_history.csv"'

        writer = csv.writer(response)
        writer.writerow(["Book Title", "Issue Date", "Due Date", "Return Date", "Fine", "Status"])

        for entry in issued_books:
            writer.writerow([
                entry.book.title,
                entry.issue_date,
                entry.due_date,
                entry.return_date if entry.return_date else "Not Returned",
                entry.fine,
                "Returned" if entry.return_date else "Pending"
            ])

        return response

    # 🔹 Stats
    returned_count = issued_books.filter(return_date__isnull=False).count()
    pending_count = issued_books.filter(return_date__isnull=True).count()
    total_fine = sum(b.fine for b in issued_books)

    context = {
        "student": student,
        "issued_books": issued_books,
        "returned_count": returned_count,
        "pending_count": pending_count,
        "total_fine": total_fine,
        "today": now().date(),
    }
    return render(request, "books/books_history.html", context)