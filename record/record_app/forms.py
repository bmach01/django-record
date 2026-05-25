from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Channel, Message, PrivateMessage

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Imię'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwisko'
        })
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Opis profilu (opcjonalnie)',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'description', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa użytkownika'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Powtórz hasło'
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ta nazwa użytkownika jest już zajęta.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ten adres email jest już zarejestrowany.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.description = self.cleaned_data.get('description', '')
        if commit:
            user.save()
        return user


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ('name', 'description', 'channel_type', 'is_public')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa kanału',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Opis kanału (opcjonalnie)',
                'rows': 3
            }),
            'channel_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Nazwa kanału jest wymagana.")
        if len(name) < 3:
            raise forms.ValidationError("Nazwa kanału musi mieć co najmniej 3 znaki.")
        return name


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Napisz wiadomość...',
                'rows': 2
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise forms.ValidationError("Wiadomość nie może być pusta.")
        return content


class PrivateMessageForm(forms.ModelForm):
    class Meta:
        model = PrivateMessage
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Napisz wiadomość prywatną...',
                'rows': 2
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise forms.ValidationError("Wiadomość nie może być pusta.")
        return content


class StartPrivateConversationForm(forms.Form):
    username = forms.CharField(
        label='Wybierz użytkownika',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'user-options',
            'autocomplete': 'off',
            'placeholder': 'Wpisz nazwę użytkownika'
        })
    )
    
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user:
            self.user_queryset = User.objects.exclude(id=current_user.id)
        else:
            self.user_queryset = User.objects.all()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username or not username.strip():
            raise forms.ValidationError("Wybierz użytkownika.")

        try:
            return self.user_queryset.get(username=username.strip())
        except User.DoesNotExist:
            raise forms.ValidationError("Nie znaleziono użytkownika o takiej nazwie.")

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('username')
        if user:
            cleaned_data['user'] = user
        return cleaned_data
