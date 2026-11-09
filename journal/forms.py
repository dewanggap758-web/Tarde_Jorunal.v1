from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import TradeLog

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class TradeLogForm(forms.ModelForm):
    class Meta:
        model = TradeLog
        # Field 'account' dihapus dari sini agar form lebih ringkas
        fields = ['pair', 'order_type', 'lot_size', 'entry_price', 'exit_price', 'strategy', 'emotion', 'notes']