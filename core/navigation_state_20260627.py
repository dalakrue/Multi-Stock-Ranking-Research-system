"""Single application-shell navigation state machine.

Only this module owns top-level page transitions. Page renderers may keep local
field/section state, but they must not overwrite ``active_page``.
"""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping
import time

UNIFIED_PAGE = "Multi-Stock Ranking Research System"
VALID_PAGES: tuple[str, ...] = (UNIFIED_PAGE,)
LEGACY_WORKSPACE_ROUTES: dict[str, str] = {
    "Settings": "System Controls & Run",
    "Home": "Ranking Command Center",
    "Lunch": "Ranking Command Center",
    "Data Visualization": "Ranking Command Center",
    "Metric": "Ranking Command Center",
    "Power BI": "Ranking Command Center",
    "PowerBI": "Ranking Command Center",
    "AI Assistant": "Multi-Stock Ranking AI Assistant",
    "Research": "Multi-Stock Ranking Data Analysis",
    "Morning": "Preserved Original Workspaces",
    "Doo Prime": "Preserved Original Workspaces",
    "Dinner": "Preserved Original Workspaces",
    "Regime": "Preserved Original Workspaces",
    "Field 4 to 9": "Preserved Original Workspaces",
    "Field 456+789": "Preserved Original Workspaces",
    "Field 456": "Preserved Original Workspaces",
    "Field 789": "Preserved Original Workspaces",
    "Dinner Combined": "Preserved Original Workspaces",
    "Other": "Preserved Original Workspaces",
}
ALIASES: dict[str, str] = {
    name: UNIFIED_PAGE for name in LEGACY_WORKSPACE_ROUTES
}


def normalize_page(page: Any, default: str = UNIFIED_PAGE) -> str:
    fallback = ALIASES.get(str(default or "").strip(), str(default or "").strip())
    if fallback not in VALID_PAGES:
        fallback = UNIFIED_PAGE
    text = str(page or fallback).strip() or fallback
    text = ALIASES.get(text, text)
    return text if text in VALID_PAGES else fallback


def _workspace_for_legacy(page: Any, subpage: str = "") -> str | None:
    raw = str(page or "").strip()
    sub = str(subpage or "").strip().lower()
    if raw == "Research":
        if "assistant" in sub:
            return "Multi-Stock Ranking AI Assistant"
        if "knn" in sub or "greedy" in sub:
            return "Multi-Stock Ranking Data Mining"
        if "nlp" in sub:
            return "Multi-Stock Ranking NLP"
        return "Multi-Stock Ranking Data Analysis"
    return LEGACY_WORKSPACE_ROUTES.get(raw)


def _set_workspace_route(state: MutableMapping[str, Any], page: Any, subpage: str = "") -> None:
    workspace = _workspace_for_legacy(page, subpage)
    if workspace:
        state["multi_stock_research_workspace"] = workspace
        state["multi_stock_research_workspace_20260729"] = workspace


def initialize_navigation(state: MutableMapping[str, Any]) -> str:
    """Initialize once. Legacy keys may seed the page but never override it later."""
    raw_page = state.get("active_page") if "active_page" in state else state.get("tab_choice")
    if str(raw_page or "").strip() != UNIFIED_PAGE:
        legacy_subpage = str(
            state.get("active_subpage")
            or (state.get("research_inner_tab") if str(raw_page or "").strip() == "Research" else "")
            or ""
        )
        _set_workspace_route(state, raw_page, legacy_subpage)
    if "active_page" not in state:
        state["active_page"] = normalize_page(state.get("tab_choice"), UNIFIED_PAGE)
    else:
        state["active_page"] = normalize_page(state.get("active_page"), UNIFIED_PAGE)
    state.setdefault("requested_page", None)
    state.setdefault("requested_subpage", "")
    state.setdefault("active_subpage", "")
    state.setdefault("active_lunch_field", None)
    state.setdefault("active_dinner_field", None)
    state.setdefault("menu_open", False)
    state.setdefault("navigation_generation", 0)
    _mirror_legacy(state)
    return str(state["active_page"])


def request_page(
    state: MutableMapping[str, Any],
    page: Any,
    subpage: str = "",
    *,
    lunch_field: Any = None,
    dinner_field: Any = None,
    reason: str = "user_navigation",
    close_menu: bool = True,
) -> dict[str, Any]:
    """Queue a route transaction. It is committed before page rendering."""
    raw_page = str(page or "").strip()
    _set_workspace_route(state, raw_page, subpage)
    target = normalize_page(page)
    state["requested_page"] = target
    state["requested_subpage"] = str(subpage or "")
    if lunch_field is not None:
        state["requested_lunch_field"] = lunch_field
    if dinner_field is not None:
        state["requested_dinner_field"] = dinner_field
    state["navigation_request_reason"] = str(reason or "navigation")
    state["navigation_request_timestamp"] = time.time()
    state["ui_navigation_click_ts"] = state["navigation_request_timestamp"]
    state["fast_tab_switch_active"] = True
    if close_menu:
        state["menu_open"] = False
        state["new7_main_menu_drawer_open"] = False
    return {
        "page": target,
        "subpage": str(subpage or ""),
        "reason": state["navigation_request_reason"],
    }


def commit_requested_page(state: MutableMapping[str, Any]) -> str:
    """Commit at most one queued route and return the authoritative page."""
    initialize_navigation(state)
    requested = state.get("requested_page")
    if requested not in (None, ""):
        target = normalize_page(requested)
        subpage = str(state.get("requested_subpage") or "")
        old_page = normalize_page(state.get("active_page"))
        old_subpage = str(state.get("active_subpage") or "")
        state["active_page"] = target
        state["active_subpage"] = ""
        if "requested_lunch_field" in state:
            state["active_lunch_field"] = state.pop("requested_lunch_field")
        if "requested_dinner_field" in state:
            state["active_dinner_field"] = state.pop("requested_dinner_field")
        state["requested_page"] = None
        state["requested_subpage"] = ""
        if target != old_page or subpage != old_subpage:
            state["navigation_generation"] = int(state.get("navigation_generation", 0) or 0) + 1
        state["navigation_committed_at"] = time.time()
    else:
        state["active_page"] = normalize_page(state.get("active_page"))
    _mirror_legacy(state)
    return str(state["active_page"])


def navigate_now(
    state: MutableMapping[str, Any],
    page: Any,
    subpage: str = "",
    *,
    lunch_field: Any = None,
    dinner_field: Any = None,
    reason: str = "user_navigation",
    close_menu: bool = True,
) -> str:
    request_page(
        state, page, subpage, lunch_field=lunch_field, dinner_field=dinner_field,
        reason=reason, close_menu=close_menu,
    )
    return commit_requested_page(state)


def _mirror_legacy(state: MutableMapping[str, Any]) -> None:
    page = normalize_page(state.get("active_page"))
    state["active_page"] = page
    state["tab_choice"] = page
    state["active_subpage"] = ""


def navigation_snapshot(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "active_page": normalize_page(state.get("active_page")),
        "active_subpage": str(state.get("active_subpage") or ""),
        "requested_page": state.get("requested_page"),
        "navigation_generation": int(state.get("navigation_generation", 0) or 0),
        "menu_open": bool(state.get("menu_open", False)),
    }


__all__ = [
    "UNIFIED_PAGE", "VALID_PAGES", "ALIASES", "LEGACY_WORKSPACE_ROUTES",
    "normalize_page", "initialize_navigation",
    "request_page", "commit_requested_page", "navigate_now", "navigation_snapshot",
]
