from django import forms
from .models import DebateRoom

class DebateRoomForm(forms.ModelForm):
    class Meta:
        model = DebateRoom
        fields = ['title','topic','description','is_private','format','allow_entry']
        widgets = {
            'description' : forms.Textarea(attrs = {'rows':3}),
            'allow_entry' : forms.CheckboxInput(),
        }