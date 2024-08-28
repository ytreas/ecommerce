from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView, signup 


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/add_review/', views.add_review, name='add_review'),
    path('signup/', signup, name='signup'), 
    path('',views.store, name="store"),
    path('cart/',views.cart, name="cart"),
    path('checkout/',views.checkout, name="checkout"),
    path('checkout/success/', views.success_page, name='success_page'),
    path('update_item/',views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="update_item"),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
]