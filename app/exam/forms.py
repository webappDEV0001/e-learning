from django import forms

class ExamImportForm(forms.Form):
    """
    This form handle the import file data.
    """

    csv_file = forms.FileField(label="file")