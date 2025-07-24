from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.TaxeListView.as_view(), name='taxes_list'),
    path('taxes/<int:pk>/', views.TaxeDetailView.as_view(), name='tax_detail'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='taxes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('panier/', views.PanierView.as_view(), name='panier'),
    path('payer/', views.PayerView.as_view(), name='payer'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('mes-paiements/', views.MesPaiementsView.as_view(), name='mes_paiements'),
]
