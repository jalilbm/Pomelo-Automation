from django.urls import path
from . import views

urlpatterns = [
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("api/settings/", views.SettingsView.as_view(), name="settings"),
    path(
        "api/user/logs/",
        views.UserLogViewSet.as_view({"get": "list"}),
        name="user_logs",
    ),
    path(
        "api/user/work_groups/", views.WorkGroupsView.as_view(), name="get_work_groups"
    ),
    path(
        "api/user/update_work_groups/",
        views.WorkGroupsView.as_view(),
        name="update_work_groups",
    ),
    path(
        "api/user/work_groups/change/",
        views.WorkGroupsView.as_view(),
        name="change_work_groups",
    ),
    # path('api/timeframe/<int:pk>/', views.TimeframeView.as_view(), name='timeframe-detail'),
    path("api/timeframe/", views.TimeframeView.as_view(), name="timeframe-list-create"),
]
