from django import forms

from .models import Pagamento

_INPUT = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 "
    "text-sm outline-none ring-blue-400 focus:ring"
)


class PagamentoCreateForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["valor", "metodo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": _INPUT})


class PagamentoConfirmForm(forms.Form):
    metodo = forms.ChoiceField(
        choices=Pagamento.METODO_CHOICES,
        widget=forms.Select(attrs={"class": _INPUT}),
        label="Método de pagamento",
    )
    provider_payment_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": _INPUT, "placeholder": "ID externo (opcional)"}),
        label="ID do pagamento",
    )
