from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('about/', views.about_view, name='about'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add-trade/', views.add_trade_view, name='add_trade'), # <--- Tambahkan ini
    path('download/trade-recap/', views.download_trade_recap, name='download_trade_recap'),
]   
