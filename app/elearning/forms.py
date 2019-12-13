
from elearning.models import ELearning
from django import forms

class ElearningForm(forms.ModelForm):
    """
    This form handle the elearning data.
    """
    EXAM = 'exam'
    ELEARNING = 'elearning'
    # ELEARNING_NS = 'elearning_ns'

    TYPES = [
        (ELEARNING, 'E-learning')
        # (ELEARNING_NS, 'E-learning (no slides)')
    ]

    exam_type = forms.ChoiceField(choices = TYPES,  widget=forms.Select())


    class Meta:
        model = ELearning
        fields = '__all__'



class ElearningImportForm(forms.Form):
    """
    This form handle the import file data.
    """

    csv_file = forms.FileField(label="file")


class PresentationImportForm(forms.Form):
    """
    This form handle the import file data.
    """

    csv_file = forms.FileField(label="file")