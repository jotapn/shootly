from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm

from deliveries.models import ConfiguracaoMarcaDagua

from .models import PerfilFotografo, User
from .tasks import task_send_mail_sendpulse

_INPUT = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 "
    "text-sm outline-none ring-blue-400 focus:ring"
)


class PerfilFotografoForm(forms.ModelForm):
    class Meta:
        model = PerfilFotografo
        fields = ["nome_empresa", "logo", "cor_primaria", "cor_secundaria", "fonte_titulo", "tema"]
        widgets = {
            "nome_empresa":   forms.TextInput(attrs={"class": _INPUT}),
            "cor_primaria":   forms.TextInput(attrs={"type": "color", "class": "h-10 w-20 rounded cursor-pointer border border-slate-300"}),
            "cor_secundaria": forms.TextInput(attrs={"type": "color", "class": "h-10 w-20 rounded cursor-pointer border border-slate-300"}),
            "fonte_titulo":   forms.Select(attrs={"class": _INPUT}),
            "tema":           forms.Select(attrs={"class": _INPUT}),
        }


class MarcaDaguaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoMarcaDagua
        fields = ["arquivo_png", "modo", "opacidade", "tamanho_pct", "posicao", "rotacao", "espacamento_pct"]
        widgets = {
            "modo": forms.Select(attrs={"class": _INPUT}),
            "opacidade": forms.NumberInput(attrs={"type": "range", "min": 0, "max": 100}),
            "tamanho_pct": forms.NumberInput(attrs={"type": "range", "min": 5, "max": 50}),
            "posicao": forms.Select(attrs={"class": _INPUT}),
            "rotacao": forms.NumberInput(attrs={"type": "range", "min": -90, "max": 90}),
            "espacamento_pct": forms.NumberInput(attrs={"type": "range", "min": 0, "max": 30}),
        }


class LoginForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            if not self.user:
                raise forms.ValidationError("E-mail ou senha invalidos.")
        return cleaned_data

    def get_user(self):
        return getattr(self, "user", None)


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class SendPulsePasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        users = list(self.get_users(email))
        if not users:
            raise forms.ValidationError(
                "Nao encontramos uma conta ativa com esse e-mail."
            )
        return email

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        task_send_mail_sendpulse(
            "Recuperacao de senha | Shootly",
            "email/reset_password.html",
            email_to=to_email,
            email=context["email"],
            site_name=context["site_name"],
            domain=context["domain"],
            uid=context["uid"],
            token=context["token"],
            protocol=context["protocol"],
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css_classes = (
            "block w-full rounded-md border border-slate-300 px-3 py-2 "
            "outline-none ring-blue-400 focus:ring"
        )
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": css_classes})

