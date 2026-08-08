from __future__ import annotations


def render(view_model) -> None:
    context = view_model["context"]
    from ui.lunch_field13_regime_lifecycle import render_field13
    render_field13(context.history_repository.state)
