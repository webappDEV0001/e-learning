from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class ExamConfig(AppConfig):
    name = 'exam'
    verbose_name = _('exam')

    def ready(self):
        import exam.signals