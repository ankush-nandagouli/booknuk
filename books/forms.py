from django import forms
from .models import Book, IssuedBook
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from datetime import timedelta
User = get_user_model()
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'category',
            'isbn',
            'description',
            'available',
            'cover_image',
            'pdf_file',
            'total_copies',
            'available_copies'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter a brief summary'}),
            'title': forms.TextInput(attrs={'placeholder': 'Book title'}),
            'author': forms.TextInput(attrs={'placeholder': 'Author name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image and image.size > 1 * 1024 * 1024:  # 1 MB limit
            raise forms.ValidationError("Cover image size should not exceed 1 MB.")
        return image

    def clean_pdf_file(self):
        pdf = self.cleaned_data.get('pdf_file')
        if pdf and pdf.size > 5 * 1024 * 1024:  # 5 MB limit
            raise forms.ValidationError("PDF file size should not exceed 5 MB.")
        return pdf

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total_copies")
        available = cleaned_data.get("available_copies")

        if available > total:
            raise forms.ValidationError("Available copies cannot be greater than total copies.")
        return cleaned_data

# Manual bulk add form (without PDF for speed; can include if you want)
class ManualBulkBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title", "author", "category", "isbn", "description",
            "total_copies", "available_copies", "cover_image"
        ]

ManualBulkBookFormSet = modelformset_factory(
    Book,
    form=ManualBulkBookForm,
    extra=5,
    can_delete=True,
)

class IssueBookForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=User.objects.all())
    book = forms.ModelChoiceField(queryset=Book.objects.filter(available_copies__gt=0))

    class Meta:
        model = IssuedBook
        fields = ['student', 'book']


    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.issue_date:
            instance.due_date = instance.issue_date + timedelta(days=14)  # auto set
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        book = cleaned_data.get("book")

        if student and book:
            # Check if same book is already issued and not returned
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