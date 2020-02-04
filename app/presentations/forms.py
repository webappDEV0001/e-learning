from django import forms

class PresentationImportForm(forms.Form):
    """
    This form handle the import file data.
    """

    csv_file = forms.FileField(label="file")