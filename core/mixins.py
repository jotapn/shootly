from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404


class FotografoMixin(LoginRequiredMixin):
    """
    Garante login e filtra querysets pelo fotografo=request.user (IDOR protection).
    Todos os CBVs do painel autenticado herdam deste mixin.
    """

    def get_queryset(self):
        return super().get_queryset().filter(fotografo=self.request.user)

    def get_job_for_fotografo(self, job_pk):
        from jobs.models import Job
        return get_object_or_404(Job, pk=job_pk, fotografo=self.request.user)
