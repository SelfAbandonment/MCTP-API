from __future__ import annotations

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.urls import reverse

from mctp_api.auth.models import MicrosoftAccount
from mctp_api.community.models import Announcement

User = get_user_model()


def dashboard_callback(request, context):
    """Small operator-facing stats for the Unfold dashboard."""
    context.update(
        {
            "dashboard_cards": [
                {
                    "label": "玩家",
                    "value": User.objects.count(),
                    "url": reverse("admin:auth_user_changelist"),
                    "icon": "group",
                },
                {
                    "label": "公告",
                    "value": Announcement.objects.count(),
                    "url": reverse("admin:community_announcement_changelist"),
                    "icon": "campaign",
                },
                {
                    "label": "微软绑定",
                    "value": SocialAccount.objects.filter(provider="microsoft").count(),
                    "url": reverse("admin:socialaccount_socialaccount_changelist"),
                    "icon": "link",
                },
                {
                    "label": "旧版绑定",
                    "value": MicrosoftAccount.objects.count(),
                    "url": reverse("admin:mctp_auth_microsoftaccount_changelist"),
                    "icon": "history",
                },
            ],
        }
    )
    return context
