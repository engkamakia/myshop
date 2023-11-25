from django.urls import path, include
from . import views

app_name = "payment"

urlpatterns = [
    #path('', views.home, name='home'),
    # path('daraja/stk-push', views.stk_push_callback, name='mpesa_stk_push_callback'),
    # path('daraja/c2b', views.c2b_callback, name='c2b_callback'),
    path('initiate/', views.initiate_stk_push, name='payment'),
    path('access/token', views.get_access_token, name='get_mpesa_access_token'),
    path('query/', views.query_stk_status, name='query_stk_status'),
    path('callback', views.process_stk_callback, name='mpesa_callback'),
    path('payment/', views.payment, name='payment'),
]