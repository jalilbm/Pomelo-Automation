from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path(
        "user/logs/",
        views.UserLogViewSet.as_view({"get": "list"}),
        name="user_logs",
    ),
    path("user/work_groups/", views.WorkGroupsView.as_view(), name="get_work_groups"),
    path(
        "user/update_work_groups/",
        views.WorkGroupsView.as_view(),
        name="update_work_groups",
    ),
    path(
        "user/work_groups/change/",
        views.WorkGroupsView.as_view(),
        name="change_work_groups",
    ),
    # path('timeframe/<int:pk>/', views.TimeframeView.as_view(), name='timeframe-detail'),
    path("timeframe/", views.TimeframeView.as_view(), name="timeframe-list-create"),
]
