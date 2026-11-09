from django.db import models
from django.contrib.auth.models import User

class TradingAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    broker = models.CharField(max_length=100, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class TradeLog(models.Model):
    ORDER_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, null=True, blank=True)
    pair = models.CharField(max_length=20, default="XAUUSD")
    order_type = models.CharField(max_length=4, choices=ORDER_CHOICES)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lot_size = models.DecimalField(max_digits=5, decimal_places=2)
    pnl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    strategy = models.CharField(max_length=100, blank=True, null=True)
    emotion = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pair} - {self.order_type}"