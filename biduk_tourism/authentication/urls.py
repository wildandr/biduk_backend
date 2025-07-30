from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserDetailView,
    ChangePasswordView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('user', UserDetailView.as_view(), name='user-detail'),
    path('password/change', ChangePasswordView.as_view(), name='change-password'),
    path('password/reset', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('password/reset/confirm', ConfirmPasswordResetView.as_view(), name='confirm-password-reset'),
]
