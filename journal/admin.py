from django.contrib import admin
from .models import TradingAccount, TradeLog

admin.site.register(TradingAccount)
admin.site.register(TradeLog)