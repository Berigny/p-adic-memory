"""Lightweight Streamlit front-end backed by the declarative spec."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from p_adic_memory.streamlit_spec import get_streamlit_spec


SPEC = get_streamlit_spec()


def _sidebar_widget(key: str, cfg: Dict[str, Any]) -> Any:
    label = cfg.get("label", key.replace("_", " ").title())
    widget_type = cfg.get("type", "text")

    if widget_type == "select":
        options = cfg.get("options", ())
        default = cfg.get("default")
        index = options.index(default) if default in options else 0
        return st.sidebar.selectbox(label, options, index=index, key=key)

    if widget_type == "number":
        default = cfg.get("default", 0)
        min_val = cfg.get("min", default)
        max_val = cfg.get("max", default)
        step = cfg.get("step", 1)
        return st.sidebar.number_input(label, value=default, min_value=min_val, max_value=max_val, step=step, key=key)

    if widget_type == "slider":
        min_val = cfg.get("min", 0)
        max_val = cfg.get("max", 1000 if isinstance(min_val, int) else 1.0)
        default = cfg.get("default", min_val)
        step = cfg.get("step", 1 if isinstance(min_val, int) else 0.01)
        return st.sidebar.slider(label, min_value=min_val, max_value=max_val, value=default, step=step, key=key)

    if widget_type == "checkbox_group":
        options = cfg.get("options", ())
        return st.sidebar.multiselect(label, options, default=list(options), key=key)

    if widget_type == "toggle":
        default = cfg.get("default", False)
        return st.sidebar.checkbox(label, value=default, key=key)

    if widget_type == "file_uploader":
        accept = cfg.get("accept")
        return st.sidebar.file_uploader(label, type=accept, key=key)

    if widget_type == "button_group":
        buttons = cfg.get("buttons", ())
        return st.sidebar.radio(label, buttons, key=key)

    return st.sidebar.text_input(label, key=key)


def render_sidebar() -> Dict[str, Any]:
    st.sidebar.header("Configuration")
    state: Dict[str, Any] = {}
    for key, cfg in SPEC["controls"].items():
        state[key] = _sidebar_widget(key, cfg)
    return state


def render_main(state: Dict[str, Any]) -> None:
    st.title("Dual-substrate Benchmark Harness")
    st.caption("Interactive shell powered by the declarative Streamlit spec")

    st.subheader("Selections")
    st.json(state)

    st.subheader("Available Charts")
    for chart_key, chart_cfg in SPEC["charts"].items():
        with st.expander(chart_cfg["title"], expanded=False):
            st.write({"type": chart_cfg.get("type"), **{k: v for k, v in chart_cfg.items() if k not in {"title", "type"}}})

    st.subheader("Operational Notes")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Interactions**")
        st.json(SPEC["interactions"])
        st.markdown("**Performance**")
        st.json(SPEC["performance"])
    with col2:
        st.markdown("**Data Model**")
        st.json(SPEC["data_model"])
        st.markdown("**Security**")
        st.json(SPEC["security"])

    st.subheader("Wishlist")
    st.json(SPEC["nice_to_have"])


def main() -> None:
    state = render_sidebar()
    render_main(state)


if __name__ == "__main__":
    main()
