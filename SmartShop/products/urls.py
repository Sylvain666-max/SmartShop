from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home, name='home'),
    path('produit/<slug:slug>/', views.product_detail, name='product_detail'),
    path('categorie/<slug:slug>/', views.category_view, name='category'),
    path('vote/<int:product_id>/', views.vote_platform, name='vote'),
]