from django.urls import path
from .views import (
    RegisterUser, LoginUser,
    MyTokenRefreshView, Logout,
    GetUserInfo, RequestResetCode,
    VerifyResetCode, ResetPassword,
    UpdateUser, AllInterests,
    UpdateUserInterests
)
urlpatterns = [
    path('register/', RegisterUser),
    path('token/', LoginUser.as_view()),
    path('token/refresh/', MyTokenRefreshView.as_view()),
    path('logout/', Logout),

    path('get-user-info/', GetUserInfo),

    path('password-reset/request-reset-code/', RequestResetCode),
    path('password-reset/verify-reset-code/', VerifyResetCode),
    path('password-reset/reset-password-with-code/', ResetPassword),

    path('update-user-info/', UpdateUser),

    path('all-interests/', AllInterests),
    path('update-user-interests/', UpdateUserInterests),
]