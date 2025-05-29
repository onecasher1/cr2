from django import forms
from .models import Patient, Appointment # Добавим AppointmentForm для примера
from django.utils import timezone

class PatientForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Дата рождения"
    )
    class Meta:
        model = Patient
        fields = ['last_name', 'first_name', 'middle_name', 'date_of_birth',
                  'contact_phone', 'email', 'address', 'insurance_policy_number', 'notes']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+79001234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'patient@example.com'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class PatientSearchForm(forms.Form):
    query = forms.CharField(
        label='Найти пациента',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО, телефон или email...'})
    )

class AppointmentForm(forms.ModelForm):
    appointment_datetime = forms.DateTimeField(
        label="Дата и время приема",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        initial=timezone.now().replace(second=0, microsecond=0) # Начальное значение
    )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_datetime', 'reason_for_visit', 'detailed_reason', 'status']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'reason_for_visit': forms.TextInput(attrs={'class': 'form-control'}),
            'detailed_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор врачей только активными
        self.fields['doctor'].queryset = self.fields['doctor'].queryset.filter(is_active=True)
        # Можно добавить ограничения для пациента, если нужно

    def clean_appointment_datetime(self):
        dt = self.cleaned_data.get('appointment_datetime')
        if dt and dt < timezone.now():
            # Для новых записей, для редактирования старых можно разрешить
            if not self.instance or not self.instance.pk: # Проверка, что это новая запись
                 raise forms.ValidationError("Нельзя записаться на прием в прошлое время.")
        # Можно добавить проверку на рабочее время клиники
        if dt.weekday() > 4: # Суббота, Воскресенье (0 - Понедельник)
             raise forms.ValidationError("Клиника не работает в выходные.")
        if not (9 <= dt.hour < 18): # Пример: часы работы с 9 до 18
             raise forms.ValidationError("Запись возможна только в рабочие часы (09:00 - 18:00).")
        return dt