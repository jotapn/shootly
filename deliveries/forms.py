from pathlib import Path

from django import forms

from jobs.models import ArquivoFoto

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff",
    ".raw", ".cr2", ".nef", ".arw", ".dng",
}
MAX_SIZE_MB = 50

_INPUT = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 "
    "text-sm outline-none ring-blue-400 focus:ring"
)


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {"multiple": True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"class": _INPUT}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]


class FotoUploadForm(forms.Form):
    arquivos = MultipleFileField(label="Fotos")
    tipo = forms.ChoiceField(
        choices=ArquivoFoto.TIPO_CHOICES,
        initial=ArquivoFoto.TIPO_BRUTA,
        widget=forms.Select(attrs={"class": _INPUT}),
        label="Tipo",
    )

    def clean_arquivos(self):
        files = self.files.getlist("arquivos")
        if not files:
            raise forms.ValidationError("Selecione ao menos um arquivo.")
        errors = []
        for f in files:
            ext = Path(f.name).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                errors.append(f"'{f.name}': extensão {ext} não permitida.")
            elif f.size > MAX_SIZE_MB * 1024 * 1024:
                errors.append(f"'{f.name}': arquivo excede {MAX_SIZE_MB} MB.")
        if errors:
            raise forms.ValidationError(errors)
        return files
