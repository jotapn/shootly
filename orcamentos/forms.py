from django import forms
from django.forms import inlineformset_factory

from clients.models import Cliente

from .models import Orcamento, OrcamentoItem, Servico

_INPUT = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 "
    "text-sm outline-none ring-blue-400 focus:ring"
)


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "descricao", "valor_padrao"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": _INPUT})


class OrcamentoForm(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ["cliente", "quantidade_fotos_incluidas", "valor_foto_extra"]
        labels = {
            "quantidade_fotos_incluidas": "Fotos incluidas no pacote",
            "valor_foto_extra": "Valor por foto extra",
        }

    def __init__(self, *args, fotografo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fotografo:
            self.fields["cliente"].queryset = Cliente.objects.filter(fotografo=fotografo)
        for field in self.fields.values():
            field.widget.attrs.update({"class": _INPUT})


class OrcamentoItemForm(forms.ModelForm):
    class Meta:
        model = OrcamentoItem
        fields = ["servico", "descricao", "valor"]

    def __init__(self, *args, fotografo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fotografo:
            self.fields["servico"].queryset = Servico.objects.filter(fotografo=fotografo)
        self.fields["servico"].required = False
        self.fields["servico"].empty_label = "— manual —"
        for name, field in self.fields.items():
            css = _INPUT
            field.widget.attrs.update({"class": css})


OrcamentoItemFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoItem,
    form=OrcamentoItemForm,
    fields=["servico", "descricao", "valor"],
    extra=1,
    can_delete=True,
    min_num=0,
)
