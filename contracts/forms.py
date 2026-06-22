from django import forms

from .models import Contrato

_INPUT = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 "
    "text-sm outline-none ring-blue-400 focus:ring"
)


class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ["conteudo"]
        widgets = {
            "conteudo": forms.Textarea(attrs={"rows": 20, "class": _INPUT + " font-mono text-xs"}),
        }


class AssinaturaForm(forms.Form):
    nome = forms.CharField(
        max_length=120,
        label="Nome completo",
        widget=forms.TextInput(attrs={"class": _INPUT}),
    )
    cpf = forms.CharField(
        max_length=20,
        label="CPF",
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "000.000.000-00"}),
    )
