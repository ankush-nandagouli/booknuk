from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentRegistration, TeacherRegistration
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class StudentRegisterForm(forms.ModelForm):

    class Meta:
        model = StudentRegistration
        fields = ['full_name', 'mobile_number', 'course', 'year_of_study', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input w-full border-blue-500 rounded-md'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-input w-full border-gray-300 rounded-md'}),
            'course': forms.Select(attrs={'id': 'course_id' ,'class': 'w-full border-gray-300 rounded-md'}),
            'year_of_study': forms.Select(attrs={'id': 'year_of_study_id', 'class': 'w-full border-gray-300 rounded-md'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea w-full border-gray-300 rounded-md', 'rows': 3}),
        }

class TeacherRegisterForm(forms.ModelForm):
    class Meta:
        model = TeacherRegistration
        fields = ['full_name', 'mobile_number', 'designation', 'department', 'address']



# 👤 Profile Update Form (for student dashboard)
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'profile_picture',
            'branch',
            'roll_number',
            'academic_session',
            'mobile_number'
        ]
        widgets = {
            'branch': forms.TextInput(attrs={'placeholder': 'e.g. Computer Science'}),
            'roll_number': forms.TextInput(attrs={'placeholder': 'e.g. CS21045'}),
            'academic_session': forms.TextInput(attrs={'placeholder': 'e.g. 2021-2025'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'e.g. 0000000000'}),
        }

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get("roll_number")
        if roll_number:
            qs = CustomUser.objects.filter(roll_number=roll_number).exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("This enrollment/roll number is already registered.")
        return roll_number



# 🛠 Admin Update Form (optional, useful if customizing admin)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'



class LibrarianCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "mobile_number", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "librarian"
        user.set_password(self.cleaned_data["password"])  # hash password
        if commit:
            user.save()
        return user

class LibrarianProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "mobile_number",
            "profile_picture",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Enter first name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Enter last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter email address"}),
            "mobile_number": forms.TextInput(attrs={"placeholder": "Enter mobile number"}),
        }