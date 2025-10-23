import csv
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .forms import ProfileForm, LibrarianProfileUpdateForm
from .forms import CustomUserCreationForm, StudentRegisterForm, TeacherRegisterForm
from .models import CustomUser, StudentRegistration
from books.models import Book, IssuedBook
from django.utils.timezone import now

def register(request):
    return render(request, 'accounts/register.html')

def student_register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = StudentRegisterForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'student'
            user.course = profile_form.cleaned_data['course']
            user.year_of_study = profile_form.cleaned_data['year_of_study']
            user.is_active = False  # wait for librarian approval
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            login(request, user)
            messages.success(request, 'Registration successful! Wait for admin approval.')
            return redirect('home')
    else:
        user_form = CustomUserCreationForm()
        profile_form = StudentRegisterForm()

    return render(request, 'accounts/student_register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def teacher_register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = TeacherRegisterForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Step 1: Create user
            user = user_form.save(commit=False)
            user.role = 'teacher'
            user.is_approved = False  # Pending approval
            user.save()

            # Step 2: Link with TeacherRegistration
            teacher_profile = profile_form.save(commit=False)
            teacher_profile.user = user
            teacher_profile.save()

            messages.success(request, "Teacher registered successfully. Awaiting admin approval.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = CustomUserCreationForm()
        profile_form = TeacherRegisterForm()

    return render(request, 'accounts/teacher_register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# 🔐 General Login
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_approved:
                login(request, user)

                # Redirect based on role
                if user.role == "librarian":
                    messages.success(request, f"Welcome Librarian {user.first_name or user.username}!")
                    return redirect('librarian_dashboard')

                elif user.role == "teacher":
                    messages.success(request, f"Welcome Teacher {user.first_name or user.username}!")
                    return redirect('teacher_dashboard')

                elif user.role == "student":
                    messages.success(request, f"Welcome {user.first_name or user.username}!")
                    return redirect('profile')
            else:
                messages.warning(request, "Your account pending approval.")
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, 'accounts/login.html')

# 🚪 Logout
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')

# 👤 Profile View
@login_required
def profile(request):
    user = request.user
    student_profile = None
    if user.role == "student":
        try:
            student_profile = StudentRegistration.objects.get(user=user)
        except StudentRegistration.DoesNotExist:
            student_profile = None
    return render(request, 'accounts/profile.html', {
        'user': user,
        'student': student_profile,
    })


# Profile Update

@login_required
def profile_update(request):
    user = request.user
    form = ProfileForm(request.POST or None, request.FILES or None, instance=user)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            # Check if profile is completed after update
            if user.profile_completed:
                messages.success(request, "Your profile has been updated successfully 🎉")
                # Redirect back to home/dashboard
                return redirect("home")
            else:
                messages.warning(request, "Profile saved, but still incomplete. Please fill all required fields.")
                return redirect("profile_update")

    return render(request, "accounts/profile_update.html", {"form": form})

# 🧑‍🏫 Librarian Role Check
def is_librarian(user):
    return user.is_authenticated and user.role == 'librarian'

@login_required
def librarian_profile(request):
    if request.user.role != "librarian":
        messages.error(request, "Access denied. Only librarians can view this page.")
        return redirect("home")  # or redirect to dashboard
    return render(request, "accounts/librarian_profile.html", {"user": request.user})

@login_required
def librarian_profile_update(request):
    if request.user.role != "librarian":
        messages.error(request, "⛔ You are not authorized to access this page.")
        return redirect("home")

    if request.method == "POST":
        form = LibrarianProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Librarian profile updated successfully!")
            return redirect("librarian_profile")
    else:
        form = LibrarianProfileUpdateForm(instance=request.user)

    return render(request, "accounts/librarian_profile_update.html", {"form": form})
@login_required
@user_passes_test(is_librarian)
def librarian_dashboard(request):
    query = request.GET.get('q', '')
    session_filter = request.GET.get('session', '')

    users = CustomUser.objects.filter(is_approved=False)
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    if session_filter:
        users = users.filter(academic_session=session_filter)

    sessions = CustomUser.objects.values_list('academic_session', flat=True).distinct()

    return render(request, 'accounts/librarian_dashboard.html', {
        'users': users,
        'query': query,
        'sessions': sessions,
        'session_filter': session_filter,
    })

# ➕ View all registered students
@login_required
@user_passes_test(is_librarian)
def registered_students(request):
    query = request.GET.get('q', '')
    students = CustomUser.objects.filter(role='student', is_approved=True)

    if query:
        students = students.filter(Q(username__icontains=query) | Q(email__icontains=query))

    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/registered_students.html', {
        'page_obj': page_obj,
        'query': query,
    })

# ➕ View all registered teachers
@login_required
@user_passes_test(is_librarian)
def registered_teachers(request):
    query = request.GET.get('q', '')
    teachers = CustomUser.objects.filter(role='teacher', is_approved=True)

    if query:
        teachers = teachers.filter(Q(username__icontains=query) | Q(email__icontains=query))

    paginator = Paginator(teachers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/registered_teachers.html', {
        'page_obj': page_obj,
        'query': query,
    })

#  Approve a pending user
@login_required
@user_passes_test(is_librarian)
def approve_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_approved=False)
    user.is_active = True
    user.is_approved = True
    user.save()
    messages.success(request, f"User {user.username} approved.")
    return redirect('librarian_dashboard')

# 🗑️ Reject and delete a pending user
@login_required
@user_passes_test(is_librarian)
def reject_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_approved=False)
    username = user.username
    user.is_active = False
    user.delete()
    messages.success(request, f"User {username} has been rejected and deleted.")
    return redirect('librarian_dashboard')

# 📤 Export pending users as CSV
@login_required
@user_passes_test(is_librarian)
def export_users_csv(request):
    users = CustomUser.objects.filter(is_approved=True)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="approved-users-list.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Role', 'Academic Session', 'Mobile Number' , 'Date Joined'])

    for user in users:
        writer.writerow([user.username, user.email, user.role, user.academic_session, user.mobile_number , user.date_joined])

    return response

#  Teacher Role Check
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    # Students
    total_students = CustomUser.objects.filter(role='student').count()
    active_students = CustomUser.objects.filter(role='student', is_active=True).count()

    # Books
    overdue_books_count = IssuedBook.objects.filter(return_date__isnull=True, due_date__lt = now()).count()
    issued_books_count = IssuedBook.objects.filter(return_date__isnull=True).count()

    context = {
        'total_students': total_students,
        'active_students': active_students,
        'overdue_books_count': overdue_books_count,
        'issued_books_count': issued_books_count,
    }
    return render(request, 'accounts/teacher_dashboard.html', context)

#  Suspend a student (Teacher only)
@login_required
@user_passes_test(is_teacher)
def suspend_student(request, user_id):
    student = get_object_or_404(CustomUser, id=user_id)
    student.is_active = False
    student.save()
    messages.success(request, f"Student {student.username} suspended.")
    return redirect('teacher_dashboard')

# 🔐 Librarian Login Page
def librarian_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user and user.role == 'librarian':
            login(request, user)
            return redirect('librarian_dashboard')
        else:
            messages.error(request, "Invalid librarian credentials.")
    return render(request, 'accounts/librarian_login.html')

# 🔐 Teacher Login Page
def teacher_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user and user.role == 'teacher':
            login(request, user)
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Invalid teacher credentials.")
    return render(request, 'accounts/teacher_login.html')


#  View Pending Approvals
@login_required
@user_passes_test(is_librarian)
def pending_approvals(request):
    query = request.GET.get('q', '')

    # Filter users who are inactive (pending approval)
    users = CustomUser.objects.filter(is_approved=False, role="student" or "teacher")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    # Pagination (10 users per page)
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }

    return render(request, 'accounts/pending_approvals.html', context)

@login_required
def student_profile_view(request, user_id):
    student = get_object_or_404(CustomUser, id=user_id, role='student')

    try:
        profile = StudentRegistration.objects.get(user=student)
    except StudentRegistration.DoesNotExist:
        profile = None

    return render(request, 'accounts/student_profile.html', {
        'student': student,
        'profile': profile,
    })



#  Student Management View
@user_passes_test(is_librarian)
def student_management(request):
    students = CustomUser.objects.filter(role='student')
    return render(request, 'accounts/student_management.html', {'students': students})

#  View Student Profile
@user_passes_test(is_librarian)
def view_student_profile(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    return render(request, 'accounts/view_student_profile.html', {'student': student})

#  Suspend or Unsuspend a student
@user_passes_test(is_librarian)
def toggle_suspend_student(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    student.is_active = not student.is_active
    student.save()
    if student.is_active:
        messages.success(request, f"Activated {student.username} successfully.")
    else:
        messages.success(request, f"Suspended {student.username} successfully.")
    return redirect('student_management')