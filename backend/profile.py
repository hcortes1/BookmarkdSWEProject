"""
Profile + Friends service functions.

What you can do:
- get_profile(username=...) or get_profile(user_id=...)  -> dict (includes friends[])
- update_profile(user_id=..., bio=..., profile_image=..., favorite_books=[...], favorite_authors=[...])
- add_friend(user_id=..., friend_id=...) / remove_friend(...)

All functions accept access_token=... to run under the end-user (RLS).
"""

from __future__ import annotations

from typing import Any, Optional
from backend.supabase_client import get_client


# ---------------------- READ ---------------------- #
def get_profile(
    *,
    username: Optional[str] = None,
    user_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict[str, Any] | None:
    """
    Read one profile (joined via view v_profile_with_friends).
    Returns None if not found.
    """
    if not username and not user_id:
        raise ValueError("Provide username or user_id")

    sb = get_client(access_token)
    q = sb.table("v_profile_with_friends").select("*")
    q = q.eq("username", username) if username else q.eq("id", user_id)
    data = q.limit(1).execute().data
    return data[0] if data else None


# ---------------------- WRITE (PROFILE) ---------------------- #
def update_profile(
    *,
    user_id: str,
    bio: Optional[str] = None,
    profile_image: Optional[str] = None,
    favorite_books: Optional[list[str]] = None,
    favorite_authors: Optional[list[str]] = None,
    access_token: Optional[str] = None,
) -> dict[str, int]:
    """
    Patch fields on public.profiles for the given user_id.
    Only fields you pass are updated. favorite_* should be lists (jsonb).
    Returns {"updated": <row_count>}.
    """
    payload: dict[str, Any] = {}
    if bio is not None:
        payload["bio"] = bio
    if profile_image is not None:
        payload["profile_image"] = profile_image
    if favorite_books is not None:
        payload["favorite_books"] = favorite_books
    if favorite_authors is not None:
        payload["favorite_authors"] = favorite_authors

    if not payload:
        return {"updated": 0}

    sb = get_client(access_token)
    res = sb.table("profiles").update(payload).eq("id", user_id).execute()
    return {"updated": len(res.data)}


# ---------------------- WRITE (FRIENDS) ---------------------- #
def _canonical_pair(a: str, b: str) -> tuple[str, str]:
    """Store friendships once using sorted (min, max) order."""
    return (a, b) if a <= b else (b, a)


def add_friend(
    *, user_id: str, friend_id: str, access_token: Optional[str] = None
) -> dict[str, int]:
    """
    Insert a friendship in canonical order. If a 409 is thrown by RLS/unique
    constraints, it means it already exists.
    Returns {"inserted": <row_count>}.
    """
    u, v = _canonical_pair(user_id, friend_id)
    sb = get_client(access_token)
    res = sb.table("friends").insert({"user_id": u, "friend_id": v}).execute()
    return {"inserted": len(res.data)}


def remove_friend(
    *, user_id: str, friend_id: str, access_token: Optional[str] = None
) -> dict[str, int]:
    """
    Remove the canonical friendship pair.
    Returns {"deleted": <row_count_or_len>}.
    """
    u, v = _canonical_pair(user_id, friend_id)
    sb = get_client(access_token)
    res = sb.table("friends").delete().eq("user_id", u).eq("friend_id", v).execute()
    # some client versions return .data, some return .count
    count = getattr(res, "count", None)
    return {"deleted": count if isinstance(count, int) else len(res.data or [])}
