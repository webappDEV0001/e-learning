
import pandas
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import PresentationImportForm
from .models import Presentation

# Create your views here.
class AdminOrStaffLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is staff or admin"""

    # ---------------------------------------------------------------------------
    # dispatch
    # ---------------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

class PresentationImportView(AdminOrStaffLoginRequiredMixin, FormView):
    """
    This class handle the import data of presentation
    """

    form_class = PresentationImportForm
    template_name = "presentation_import_form.html"

    def get_success_url(self):
        success_url = reverse_lazy('admin:presentations_presentation_changelist')
        return success_url

    def form_valid(self, form):
        from os import path
        csv_file = form.cleaned_data.get("csv_file")
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)

        for i in range(len(df)):
            try:
                presentation_name = df['presentation_name'][i]
                topic = df['topic'][i]
                slide = df['slide'][i]
                presentation, crt = Presentation.objects.get_or_create(elearning=presentation_name, topic=topic,slide=slide)
            except:
                print("Skip row")
        messages.info(self.request, "your presentation data imported successfully.")
        return FormView.form_valid(self, form)

    def get_context_data(self, **kwargs):

        context = super(PresentationImportView, self).get_context_data()
        context["opts"] = Presentation._meta
        return context
