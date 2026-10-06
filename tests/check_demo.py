from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import re

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
artifacts = root / "artifacts"
artifacts.mkdir(exist_ok=True)
server = ThreadingHTTPServer(
    ("127.0.0.1", 0),
    partial(SimpleHTTPRequestHandler, directory=str(root)),
)
Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}"

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for name, width, height in (
                ("desktop", 1440, 1000),
                ("mobile", 390, 844),
            ):
                page = browser.new_page(
                    viewport={"width": width, "height": height}
                )
                errors = []
                external = []
                page.on("pageerror", lambda error: errors.append(str(error)))

                def route_request(route):
                    if route.request.url.startswith(url + "/"):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()

                page.route("**/*", route_request)
                try:
                    response = page.goto(url, wait_until="networkidle")
                    assert response.status == 200, "Page did not return HTTP 200"
                    assert page.title() == "AI Forge | DEMO"
                    assert page.get_by_role(
                        "heading", name="DEMO Project", exact=True
                    ).is_visible()
                    for machine in ("Athena-01", "Daedalus-02"):
                        assert page.get_by_role(
                            "heading", name=machine, exact=True
                        ).is_visible()

                    order = page.locator("#journal-order")
                    assert order.input_value() == "oldest", \
                        "Oldest First must be the default"

                    entries = page.locator(".journal article").evaluate_all(
                        """els => els.map(e => ({
                            cycle: e.dataset.cycle,
                            created: e.dataset.createdAt,
                            time: e.querySelector('time')?.getAttribute('datetime'),
                            label: e.querySelector('time')?.textContent,
                            stamp: Date.parse(e.dataset.createdAt)
                        }))"""
                    )
                    assert entries, "Journal is empty"
                    cycles = [e["cycle"] for e in entries]
                    assert "0" in cycles, "Cycle 0 is missing"
                    assert len(cycles) == len(set(cycles)), "Duplicate cycles"
                    for entry in entries:
                        assert re.fullmatch(r"\d+", entry["cycle"] or "")
                        assert re.fullmatch(
                            r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d"
                            r"(?:\.\d+)?[+-]\d\d:\d\d",
                            entry["created"] or "",
                        ), "Timestamp requires an explicit timezone offset"
                        assert entry["stamp"] is not None, "Invalid date"
                        assert entry["time"] == entry["created"], \
                            "Journal time does not match creation timestamp"
                        assert re.search(r"\bC[DS]T\b", entry["label"] or ""), \
                            "Display the Chicago timezone abbreviation"

                    stamps = [e["stamp"] for e in entries]
                    assert stamps == sorted(stamps), "Initial order is incorrect"

                    # Mission Control panel checks
                    mission = page.locator("section.mission")
                    assert mission.is_visible(), "Mission Control panel missing"
                    assert page.get_by_role("heading", name="MISSION CONTROL", exact=True).is_visible()
                    assert page.get_by_text("Snapshot from recorded project state — not live monitoring").is_visible()
                    for label in ("Current Goal", "Progress", "Last Completed Step", "Next Task"):
                        assert mission.locator(f".label:has-text('{label}')").is_visible(), f"Mission panel missing {label}"
                    # Recovery Checkpoint panel checks
                    for label in ("Recovery Checkpoint", "Hostname", "OS", "Git Revision Inspected", "Inspection Time (America/Chicago)"):
                        assert mission.locator(f".label:has-text('{label}')").is_visible(), f"Mission panel missing {label}"
                    assert page.get_by_text("This is a recorded snapshot of the current machine state at inspection time. It does not prove a restore occurred.").is_visible()

                    # Add browser-only fixtures so sorting is tested even
                    # when the real journal contains just one entry.
                    page.locator(".journal").evaluate("""journal => {
                        for (const date of [
                            '2099-01-01T00:00:00-06:00',
                            '2000-01-01T00:00:00-06:00'
                        ]) {
                            const card = document.createElement('article');
                            card.dataset.testFixture = 'true';
                            card.dataset.createdAt = date;
                            journal.appendChild(card);
                        }
                    }""")
                    for value, reverse in (("newest", True), ("oldest", False)):
                        order.select_option(value)
                        actual = page.locator(".journal article").evaluate_all(
                            "els => els.map(e => Date.parse(e.dataset.createdAt))"
                        )
                        assert actual == sorted(actual, reverse=reverse), \
                            f"{value} sorting failed"
                    page.locator("[data-test-fixture]").evaluate_all(
                        "els => els.forEach(e => e.remove())"
                    )
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    ), "Horizontal overflow"
                    assert not errors, f"JavaScript errors: {errors}"
                    assert not external, f"External page dependencies: {external}"
                    print(f"PASS: {name}: content, timestamps, sorting and layout")
                finally:
                    page.screenshot(
                        path=str(artifacts / f"{name}.png"), full_page=True
                    )
                    page.close()
        finally:
            browser.close()
finally:
    server.shutdown()
    server.server_close()
