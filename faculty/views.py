import logging
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.db.models import Sum
from threading import Thread

from accounts.views import is_teacher
from accounts.models import CustomUser
from books.models import IssuedBook, Book
from .forms import TeacherIssueBookForm

logger = logging.getLogger(__name__)

# -------------------------
# Async Email Sender
# -------------------------
def send_email_async(subject, message, recipients):
    try:
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
        email.send(fail_silently=False)
        logger.info(f"Email sent to {len(recipients)} recipients.")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")


# -------------------------
# Send Notifications
# -------------------------
@user_passes_test(is_teacher)
def send_notifications(request):
    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        recipients = list(CustomUser.objects.filter(role="student", is_active=True)
                          .values_list("email", flat=True))
        if not recipients:
            messages.warning(request, "⚠️ No active students to send notifications.")
            return redirect("teacher_dashboard")

        # Async send
        Thread(target=send_email_async, args=(subject, message, recipients)).start()
        messages.success(request, "✅ Notification sending started to all active students.")
        return redirect("teacher_dashboard")

    return render(request, "faculty/send_notifications.html")


# -------------------------
# Student List with Pagination
# -------------------------
@user_passes_test(is_teacher)
def student_list(request):
    q = request.GET.get("q", "")
    cursor = request.GET.get("cursor")
    limit = 10

    students = CustomUser.objects.filter(role="student").order_by("id")
    if q:
        students = students.filter(Q(username__icontains=q) | Q(email__icontains=q))
    if cursor:
        students = students.filter(id__gt=cursor)

    students = students[:limit+1]
    next_cursor = students.last().id if len(students) > limit else None
    students = students[:limit]

    return render(request, "faculty/student_list.html", {
        "students": students,
        "q": q,
        "next_cursor": next_cursor
    })


# -------------------------
# Student Profile & Book History
# -------------------------
@user_passes_test(is_teacher)
def students_profile(request, slug):
    student = get_object_or_404(CustomUser, slug=slug, role="student")
    issued_books = student.issuedbook_set.select_related("book").order_by("-issue_date")


    total_fine = sum([book.fine for book in issued_books])
    return render(request, "faculty/students_profile.html", {
        "student": student,
        "issued_books": issued_books,
        "total_fine": total_fine,
    })


# -------------------------
# Suspend / Activate Student
# -------------------------
@user_passes_test(is_teacher)
def suspend_students(request, slug):
    student = get_object_or_404(CustomUser, slug=slug, role="student")
    student.is_active = not student.is_active
    student.save()
    status = "activated" if student.is_active else "suspended"
    logger.info(f"Teacher {request.user.username} {status} student {student.username}")
    messages.success(request, f"✅ {student.username} has been {status}.")
    return redirect("faculty:student_list")


# -------------------------
# Teacher Issue Book
# -------------------------
@user_passes_test(is_teacher)
def teacher_issue_book(request):
    today = timezone.now().date()
    due_date = today + timedelta(days=14)  # 2 weeks

    if request.method == "POST":
        form = TeacherIssueBookForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            book = form.cleaned_data['book']

            # Check for duplicate issue
            if IssuedBook.objects.filter(student=student, book=book, return_date__isnull=True).exists():
                messages.warning(
                    request,
                    f"⚠️ '{book.title}' is already issued to {student.username} and not returned yet!"
                )
                return render(request, "faculty/teacher_issue_book.html", {"form": form, "today": today, "due_date": due_date})

            try:
                with transaction.atomic():
                    # Lock the book row
                    locked_book = Book.objects.select_for_update().get(pk=book.pk)
                    if locked_book.available_copies <= 0:
                        messages.error(request, f"❌ '{locked_book.title}' has no available copies to issue.")
                        return render(request, "faculty/teacher_issue_book.html", {"form": form, "today": today, "due_date": due_date})

                    # Save issued book
                    issued_book = form.save(commit=False)
                    issued_book.issue_date = today
                    issued_book.due_date = due_date
                    issued_book.issued_by = request.user
                    issued_book.save()

                    # Decrement copies
                    Book.objects.filter(pk=locked_book.pk).update(available_copies=F("available_copies") - 1)

            except Exception as e:
                logger.error(f"Error issuing book: {str(e)}")
                messages.error(request, "❌ Unexpected error occurred. Check logs.")
                return render(request, "faculty/teacher_issue_book.html", {"form": form, "today": today, "due_date": due_date})

            messages.success(request, f"✅ Book '{issued_book.book.title}' issued to {issued_book.student.username}.")
            return redirect("faculty:teacher_issue_book")
        else:
            # Inline form errors
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f"{field}: {err}")
    else:
        form = TeacherIssueBookForm()

    return render(request, "faculty/teacher_issue_book.html", {"form": form, "today": today, "due_date": due_date})
