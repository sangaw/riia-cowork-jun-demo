"""Responsive-layout Playwright tests.

Verifies that each dashboard renders correctly at three viewport sizes:

  - Desktop  1280 × 800  — sidebar visible, hamburger hidden, KPI cards present
  - Tablet    768 × 1024  — hamburger visible, sidebar starts closed, opens on click
  - Mobile    390 × 844   — hamburger visible, main content fills the viewport width

Only Chromium is used (Firefox/WebKit skipped to keep CI cost low).

Prerequisites
-------------
    pip install pytest-playwright
    playwright install chromium --with-deps

Running
-------
    pytest riia-jun-release/tests/e2e/test_responsive.py -v
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Dashboards under test
# ---------------------------------------------------------------------------
_DASHBOARDS = [
    "/dashboard/rita.html",
    "/dashboard/fno.html",
    "/dashboard/ops.html",
]

# ---------------------------------------------------------------------------
# Viewport presets
# ---------------------------------------------------------------------------
_DESKTOP = {"width": 1280, "height": 800}
_TABLET  = {"width": 768,  "height": 1024}
_MOBILE  = {"width": 390,  "height": 844}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(page: Page, base_url: str, path: str, viewport: dict) -> None:
    """Set viewport and navigate; assert HTTP 200."""
    page.set_viewport_size(viewport)
    response = page.goto(base_url + path, wait_until="domcontentloaded", timeout=60_000)
    assert response is not None, f"No response for {path}"
    assert response.status == 200, (
        f"Expected 200 for {path} at {viewport}, got {response.status}"
    )


# ---------------------------------------------------------------------------
# Desktop tests  (1280 × 800)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_desktop_page_loads(page: Page, base_url: str, dashboard: str) -> None:
    """Dashboard returns 200 at desktop viewport."""
    _load(page, base_url, dashboard, _DESKTOP)


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_desktop_nav_toggle_hidden(page: Page, base_url: str, dashboard: str) -> None:
    """Hamburger button must NOT be visible at desktop width (CSS hides it >768px)."""
    _load(page, base_url, dashboard, _DESKTOP)
    nav_toggle = page.locator("#nav-toggle")
    expect(nav_toggle).not_to_be_visible()


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_desktop_sidebar_visible(page: Page, base_url: str, dashboard: str) -> None:
    """Sidebar must be visible and have a non-zero rendered width at desktop."""
    _load(page, base_url, dashboard, _DESKTOP)
    sidebar = page.locator(".sidebar").first
    expect(sidebar).to_be_visible()
    box = sidebar.bounding_box()
    assert box is not None, ".sidebar has no bounding box"
    assert box["width"] > 0, f".sidebar width is 0 at desktop: {box}"


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_desktop_kpi_elements_present(page: Page, base_url: str, dashboard: str) -> None:
    """At least one .kpi-row or .kpi element must be present in the DOM."""
    _load(page, base_url, dashboard, _DESKTOP)
    kpi_count = page.locator(".kpi-row, .kpi").count()
    assert kpi_count > 0, (
        f"No .kpi-row or .kpi elements found in {dashboard} at desktop"
    )


# ---------------------------------------------------------------------------
# Tablet tests  (768 × 1024)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_tablet_page_loads(page: Page, base_url: str, dashboard: str) -> None:
    """Dashboard returns 200 at tablet viewport."""
    _load(page, base_url, dashboard, _TABLET)


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_tablet_nav_toggle_visible(page: Page, base_url: str, dashboard: str) -> None:
    """Hamburger button must be visible at tablet width (≤768px)."""
    _load(page, base_url, dashboard, _TABLET)
    nav_toggle = page.locator("#nav-toggle")
    expect(nav_toggle).to_be_visible()


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_tablet_sidebar_starts_closed(page: Page, base_url: str, dashboard: str) -> None:
    """Sidebar must NOT have class 'open' on initial page load at tablet."""
    _load(page, base_url, dashboard, _TABLET)
    sidebar = page.locator(".sidebar").first
    classes = sidebar.get_attribute("class") or ""
    assert "open" not in classes.split(), (
        f".sidebar unexpectedly has 'open' class on load: '{classes}'"
    )


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_tablet_hamburger_opens_sidebar(page: Page, base_url: str, dashboard: str) -> None:
    """Clicking hamburger must add class 'open' to .sidebar."""
    _load(page, base_url, dashboard, _TABLET)
    nav_toggle = page.locator("#nav-toggle")
    sidebar = page.locator(".sidebar").first

    nav_toggle.click()

    # Allow up to 500 ms for CSS transition / JS class toggle.
    expect(sidebar).to_have_class(re.compile(r"(^|\s)open(\s|$)"), timeout=500)


# ---------------------------------------------------------------------------
# Mobile tests  (390 × 844)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_mobile_page_loads(page: Page, base_url: str, dashboard: str) -> None:
    """Dashboard returns 200 at mobile viewport."""
    _load(page, base_url, dashboard, _MOBILE)


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_mobile_nav_toggle_visible(page: Page, base_url: str, dashboard: str) -> None:
    """Hamburger button must be visible at mobile width."""
    _load(page, base_url, dashboard, _MOBILE)
    nav_toggle = page.locator("#nav-toggle")
    expect(nav_toggle).to_be_visible()


@pytest.mark.parametrize("dashboard", _DASHBOARDS)
def test_mobile_main_content_fills_width(page: Page, base_url: str, dashboard: str) -> None:
    """Main content area must fill most of the viewport (sidebar off-canvas).

    We accept 'most' as >= 80% of the viewport width, which rules out cases
    where the sidebar is still stealing horizontal space.
    """
    _load(page, base_url, dashboard, _MOBILE)
    main = page.locator("main, .main-content, #main-content, .content").first
    box = main.bounding_box()
    if box is None:
        pytest.skip(f"No main content element found in {dashboard}; skipping width check")
    viewport_width = _MOBILE["width"]
    assert box["width"] >= viewport_width * 0.80, (
        f"Main content width {box['width']}px is less than 80% of "
        f"viewport {viewport_width}px in {dashboard} at mobile"
    )
