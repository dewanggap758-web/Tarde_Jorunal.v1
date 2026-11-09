from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import TradeLog
from .forms import UserRegistrationForm
from django.db.models import Count, Sum
from django.db.models.functions import Cast
from django.db.models import DateField
from .forms import UserRegistrationForm, TradeLogForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import TradeLog, TradingAccount
from .forms import TradeLogForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import TradeLog
from django.utils import timezone

from .exports import build_trade_recap_pdf
from django.http import HttpResponse

def home_view(request):
    return render(request, 'journal/home.html')


@login_required(login_url='login')
def dashboard_view(request):
    # Ambil trade milik user yang login ATAU yang user-nya kosong (untuk jaga-jaga)
    trades = TradeLog.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by('-date_time')
    
    total_trades = trades.count()
    winning_trades = trades.filter(pnl__gt=0).count()
    win_rate = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0
    
    total_pnl = sum([t.pnl for t in trades if t.pnl]) or 0
    
    buy_count = trades.filter(order_type='BUY').count()
    sell_count = trades.filter(order_type='SELL').count()
    buy_percentage = round((buy_count / total_trades * 100), 1) if total_trades > 0 else 50
    sell_percentage = round((sell_count / total_trades * 100), 1) if total_trades > 0 else 50

    rr_list = []
    for t in trades:
        if t.exit_price and t.entry_price:
            diff = abs(t.exit_price - t.entry_price)
            rr_list.append(float(diff))
    avg_rr = f"1 : {sum(rr_list)/len(rr_list):.1f}" if rr_list else "1 : 2.0"

    context = {
        'trades': trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'buy_percentage': buy_percentage,
        'sell_percentage': sell_percentage,
        'avg_rr': avg_rr,
    }
    return render(request, 'journal/dashboard.html', context)

@login_required(login_url='login')
def dashboard_view(request):
    trades = TradeLog.objects.filter(user=request.user).order_by('-date_time')
    
    total_trades = trades.count()
    winning_trades = trades.filter(pnl__gt=0).count()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_pnl = sum([t.pnl for t in trades if t.pnl] ) or 0
    
    # Hitung Statistik Buy vs Sell
    buy_count = trades.filter(order_type='BUY').count()
    sell_count = trades.filter(order_type='SELL').count()
    buy_percentage = (buy_count / total_trades * 100) if total_trades > 0 else 50
    sell_percentage = (sell_count / total_trades * 100) if total_trades > 0 else 50

    # Estimasi Risk/Reward Ratio (Contoh perhitungan berdasarkan jarak entry ke exit)
    rr_list = []
    for t in trades:
        if t.exit_price and t.entry_price:
            diff = abs(t.exit_price - t.entry_price)
            rr_list.append(float(diff))
    avg_rr = f"1 : {sum(rr_list)/len(rr_list):.1f}" if rr_list else "1 : 2.0"

    context = {
        'trades': trades,
        'total_pnl': total_pnl,
        'win_rate': round(win_rate, 1),
        'total_trades': total_trades,
        'buy_percentage': round(buy_percentage, 1),
        'sell_percentage': round(sell_percentage, 1),
        'avg_rr': avg_rr,
    }
    return render(request, 'journal/dashboard.html', context)

@login_required(login_url='login')
def add_trade_view(request):
    if request.method == 'POST':
        form = TradeLogForm(request.POST, user=request.user)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.user = request.user
            # Otomatis hitung PnL sederhana jika exit price terisi
            if trade.exit_price and trade.entry_price:
                diff = trade.exit_price - trade.entry_price
                if trade.order_type == 'SELL':
                    diff = -diff
                trade.pnl = diff * trade.lot_size * 100 # Perkiraan pip value sederhana
            trade.save()
            return redirect('dashboard')
    else:
        form = TradeLogForm(user=request.user)
    return render(request, 'journal/add_trade.html', {'form': form})

def add_trade_view(request):
    if request.method == 'POST':
        form = TradeLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TradeLogForm()
    return render(request, 'journal/add_trade.html', {'form': form})

# Halaman Dashboard
@login_required(login_url='login')
def dashboard_view(request):
    trades = TradeLog.objects.filter(user=request.user).order_by('-date_time')
    total_trades = trades.count()
    winning_trades = trades.filter(pnl__gt=0).count()
    win_rate = round(winning_trades / total_trades * 100, 1) if total_trades else 0
    total_pnl = sum((trade.pnl or 0) for trade in trades) or 0

    buy_count = trades.filter(order_type='BUY').count()
    sell_count = trades.filter(order_type='SELL').count()
    buy_percentage = round(buy_count / total_trades * 100, 1) if total_trades else 50
    sell_percentage = round(sell_count / total_trades * 100, 1) if total_trades else 50

    rr_values = [
        float(abs(trade.exit_price - trade.entry_price))
        for trade in trades
        if trade.exit_price is not None
    ]
    avg_rr = f"1 : {sum(rr_values) / len(rr_values):.1f}" if rr_values else "1 : 2.0"
    
    daily_pnl = (
        TradeLog.objects.filter(
            user=request.user,
            exit_price__isnull=False,
            pnl__isnull=False,
        )
        .annotate(trade_date=Cast('date_time', DateField()))
        .values('trade_date')
        .annotate(total_pnl=Sum('pnl'), trade_count=Count('id'))
        .order_by('trade_date')
    )

    calendar_events = []
    pnl_chart_data = []
    for item in daily_pnl:
        pnl = float(item['total_pnl'] or 0)
        color = '#059669' if pnl >= 0 else '#e11d48'
        title = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        chart_date = item['trade_date']
        
        calendar_events.append({
            'title': title,
            'start': chart_date.strftime('%Y-%m-%d'),
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'extendedProps': {'tradeCount': item['trade_count']},
        })
        pnl_chart_data.append({
            'date': chart_date.strftime('%Y-%m-%d'),
            'pnl': pnl,
            'tradeCount': item['trade_count'],
        })

    context = {
        'trades': trades,
        'calendar_events': calendar_events,
        'pnl_chart_data': pnl_chart_data,
        'trade_mix_data': [buy_count, sell_count],
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'buy_percentage': buy_percentage,
        'sell_percentage': sell_percentage,
        'avg_rr': avg_rr,
    }
    return render(request, 'journal/dashboard.html', context)

# Halaman About
def about_view(request):
    return render(request, 'journal/about.html')

# Fitur Registrasi
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'journal/register.html', {'form': form})

# Fitur Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'journal/login.html', {'form': form})

@login_required(login_url='login')
def add_trade_view(request):
    trades = TradeLog.objects.filter(user=request.user)
    total_trades = trades.count()
    winning_trades = trades.filter(pnl__gt=0).count()
    buy_count = trades.filter(order_type='BUY').count()
    sell_count = trades.filter(order_type='SELL').count()
    rr_values = [
        float(abs(trade.exit_price - trade.entry_price))
        for trade in trades
        if trade.exit_price is not None
    ]

    if request.method == 'POST':
        form = TradeLogForm(request.POST)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.user = request.user  # Otomatis kaitkan ke user yang sedang login
            
            # Hitung otomatis PnL sederhana jika exit price diisi
            if trade.exit_price and trade.entry_price:
                diff = trade.exit_price - trade.entry_price
                if trade.order_type == 'SELL':
                    diff = -diff
                trade.pnl = diff * trade.lot_size * 100
                
            trade.save()
            return redirect('dashboard')
    else:
        form = TradeLogForm()

    context = {
        'form': form,
        'total_pnl': trades.aggregate(total=Sum('pnl'))['total'] or 0,
        'win_rate': round(winning_trades / total_trades * 100, 1) if total_trades else 0,
        'total_trades': total_trades,
        'buy_percentage': round(buy_count / total_trades * 100, 1) if total_trades else 50,
        'sell_percentage': round(sell_count / total_trades * 100, 1) if total_trades else 50,
        'avg_rr': f"1 : {sum(rr_values) / len(rr_values):.1f}" if rr_values else "1 : 2.0",
    }
    return render(request, 'journal/add_trade.html', context)


@login_required(login_url='login')
def download_trade_recap(request):
    trades = TradeLog.objects.filter(user=request.user).order_by('-date_time')
    pdf = build_trade_recap_pdf(request.user.username, trades)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="trade-recap-{}.pdf"'.format(
            timezone.localdate().isoformat()
        )
    )
    return response
# Fitur Logout
def logout_view(request):
    logout(request)
    return redirect('home')