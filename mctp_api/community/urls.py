from django.urls import path

from .views import (
    AnnouncementDetailView,
    AnnouncementListCreateView,
    PlayerDetailView,
    PlayerListView,
    PublicAnnouncementListView,
)

urlpatterns = [
    path("announcements/", PublicAnnouncementListView.as_view(), name="announcement-public-list"),
    path("manage/announcements/", AnnouncementListCreateView.as_view(), name="announcement-list"),
    path("manage/announcements/<int:pk>/", AnnouncementDetailView.as_view(), name="announcement-detail"),
    path("manage/players/", PlayerListView.as_view(), name="player-list"),
    path("manage/players/<int:pk>/", PlayerDetailView.as_view(), name="player-detail"),
]
