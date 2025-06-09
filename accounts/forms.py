from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User

class UserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'role', 'group', 'student_number', 'position')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].required = False
        self.fields['student_number'].required = False
        self.fields['position'].required = False

        if 'role' in self.data:
            if self.data['role'] == 'студент':
                self.fields['group'].required = True
                self.fields['student_number'].required = True
                self.fields['position'].widget = forms.HiddenInput()
            else:
                self.fields['group'].widget = forms.HiddenInput()
                self.fields['student_number'].widget = forms.HiddenInput()


    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user



class UserChangeForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'name', 'password', 'role',
            'group', 'student_number', 'position', 'is_active', 'is_staff'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].required = False
        self.fields['student_number'].required = False
        self.fields['position'].required = False

        if self.instance and self.instance.role == 'студент':
            self.fields['group'].widget = forms.TextInput()
            self.fields['student_number'].widget = forms.TextInput()
            self.fields['position'].widget = forms.HiddenInput()
        else:
            self.fields['group'].widget = forms.HiddenInput()
            self.fields['student_number'].widget = forms.HiddenInput()

