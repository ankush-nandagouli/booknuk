from django import forms
from books.models import IssuedBook
from django.contrib.auth import get_user_model
User = get_user_model()
from books.models import Book

class TeacherIssueBookForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        label="Student"
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        label="Book"
    )

    class Meta:
        model = IssuedBook
        fields = ['student', 'book']

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        book = cleaned_data.get("book")

        if student and book:
            # Checking if same book is already issued and not returned
            already_issued = IssuedBook.objects.filter(
                student=student,
                book=book,
                return_date__isnull=True  # meaning still with the student
            ).exists()

            if already_issued:
                raise forms.ValidationError(
                    f"{student.username} already has '{book.title}' issued and not returned yet."
                )

        return cleaned_data
