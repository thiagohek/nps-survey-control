from django import forms
from django.forms import inlineformset_factory
from .models import Survey, ServiceScore, Strength, Improvement


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = [
            'client', 'date_conducted', 'respondent_name',
            'respondent_role', 'nps_score', 'strengths', 'improvements',
            'comments', 'is_historical',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'date_conducted': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nps_score': forms.NumberInput(attrs={'min': 0, 'max': 10, 'class': 'form-control'}),
            'strengths': forms.CheckboxSelectMultiple,
            'improvements': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['strengths'].queryset = Strength.objects.filter(is_active=True)
        self.fields['improvements'].queryset = Improvement.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        client = cleaned.get('client')
        date = cleaned.get('date_conducted')
        if client and date:
            qs = Survey.objects.filter(client=client, date_conducted=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    'Já existe uma pesquisa para este cliente nesta data.'
                )
        return cleaned


class ServiceScoreForm(forms.ModelForm):
    class Meta:
        model = ServiceScore
        fields = ['service', 'score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 0, 'max': 10}),
        }


ServiceScoreFormSet = inlineformset_factory(
    Survey,
    ServiceScore,
    form=ServiceScoreForm,
    extra=0,
    can_delete=False,
)
