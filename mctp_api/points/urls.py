from django.urls import path

from .views import (
    GrantPointsView,
    LeaderboardView,
    ManagePointAccountListView,
    MyGrantListView,
    MyPointsView,
)

urlpatterns = [
    path("points/me/", MyPointsView.as_view(), name="points-me"),
    path("points/grants/", MyGrantListView.as_view(), name="points-grants"),
    path("points/leaderboard/", LeaderboardView.as_view(), name="points-leaderboard"),
    path("manage/points/", ManagePointAccountListView.as_view(), name="points-manage-list"),
    path("manage/points/grants/", GrantPointsView.as_view(), name="points-manage-grant"),
]
