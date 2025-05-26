from django.urls import path
from .views import (
    register_user, LoginUser,
    MyTokenRefreshView, logout_user,
    get_user_info, request_reset_code,
    verify_reset_code, reset_password,
    update_user_account, all_interests,
    update_user_interests, save_place,
    delete_saved_place, get_user_saved_places,
    get_user_search_history, delete_user_search_history,
)
urlpatterns = [
    path('register/', register_user),
    path('token/', LoginUser.as_view()),
    path('token/refresh/', MyTokenRefreshView.as_view()),
    path('logout/', logout_user),

    path('get-user-info/', get_user_info),

    path('password-reset/request-reset-code/', request_reset_code),
    path('password-reset/verify-reset-code/', verify_reset_code),
    path('password-reset/reset-password-with-code/', reset_password),

    path('update-user-info/', update_user_account),

    path('all-interests/', all_interests),
    path('update-user-interests/', update_user_interests),

    path('saved-places/<int:city_id>/', get_user_saved_places),
    path('save-place/<int:city_id>/', save_place),
    path('delete-saved-place/<int:city_id>/', delete_saved_place),

    path('search-history/', get_user_search_history),
    path('delete-search-history/', delete_user_search_history),
]