from django import forms
from .models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['name', 'saas_description', 'target_audience']
        widgets = {
            'saas_description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. A project management tool for remote teams'}),
            'target_audience': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. CTOs and Engineering Managers at startups with 10-200 employees'}),
        }
