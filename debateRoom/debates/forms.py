from django import forms
from .models import DebateRoom

class DebateRoomForm(forms.ModelForm):
    class Meta:
        model = DebateRoom
        fields = ['title','topic','description','is_private','debate_format','allow_entry']
        widgets = {
            'description' : forms.Textarea(attrs = {'rows':3}),
            'allow_entry' : forms.CheckboxInput(),
        }