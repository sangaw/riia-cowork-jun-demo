"""
Update the Engineering Confluence page (76611602) for Phase 01 Technical Analysis.

Changes:
  1. Add GET /api/v1/experience/rita/technical-commentary row to Experience Layer table.
  2. Add a Technical Analysis section note (nav item + section + ATR/RSI move).
  3. Remove the duplicate RITA Nav/Section Swap block (the previous script ran twice).
  4. Bump version date to 2026-05-14.

Run from project root:
    python project-office/confluence/_update_engineering_technical_analysis.py
"""
import urllib.request, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = Path("confluence-api-key.txt").read_text().splitlines()[1].strip()
TOKEN   = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put(path, payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PUT")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ── 1. Fetch current page ────────────────────────────────────────────────────
page    = get(f"content/{PAGE_ID}?expand=body.storage,version")
title   = page["title"]
version = page["version"]["number"]
body    = page["body"]["storage"]["value"]

print(f"Fetched: '{title}' v{version}, {len(body)} chars")
body_updated = body

# ── 2. Fix duplicate Nav/Section Swap block ──────────────────────────────────
# The block appears twice in the current page body. Remove the second occurrence.
SWAP_BLOCK_START = "<h3>RITA Dashboard &mdash; Nav/Section Swap (2026-05-11)</h3>"
first_idx  = body_updated.find(SWAP_BLOCK_START)
second_idx = body_updated.find(SWAP_BLOCK_START, first_idx + 1)

if second_idx != -1:
    # Find the end of the second block: the next <h3> or <h2> that follows it
    end_marker = "<h3>Workflow &mdash;"
    end_idx = body_updated.find(end_marker, second_idx)
    if end_idx != -1:
        duplicate = body_updated[second_idx:end_idx]
        body_updated = body_updated[:second_idx] + body_updated[end_idx:]
        print(f"OK: Removed duplicate Nav/Section Swap block ({len(duplicate)} chars)")
    else:
        print("NOTE: Could not find end marker for duplicate block — skipping removal")
else:
    print("NOTE: No duplicate Nav/Section Swap block found — already clean")

# ── 3. Add technical-commentary endpoint row to Experience Layer table ───────
MARKER_TECH_ROW = "technical-commentary-endpoint-row-2026-05-14"

if MARKER_TECH_ROW in body_updated:
    print("NOTE: technical-commentary endpoint row already present — skipping")
else:
    # Insert before the closing </tbody> of the Experience Layer table.
    # Anchor: the token-forecast row closes with </td></tr> just before </tbody></table>
    # We add immediately before the last </tbody> that follows the Experience Layer <h3>.
    EXPERIENCE_H3 = "<h3>Experience Layer &mdash; <code>api/experience/</code></h3>"
    exp_idx = body_updated.find(EXPERIENCE_H3)
    if exp_idx == -1:
        print("ERROR: Could not find Experience Layer h3 — endpoint row NOT added")
    else:
        # Find the </tbody></table> that closes this section's table
        close_tbody = body_updated.find("</tbody>\n</table>", exp_idx)
        if close_tbody == -1:
            close_tbody = body_updated.find("</tbody></table>", exp_idx)
        if close_tbody == -1:
            print("ERROR: Could not find closing </tbody> for Experience table — NOT added")
        else:
            new_row = (
                f"\n    <!-- {MARKER_TECH_ROW} -->"
                "\n    <tr><td>/api/v1/experience/rita/technical-commentary</td>"
                "<td>GET</td>"
                "<td>Technical commentary + signal summary for the active instrument. "
                "Query param: <code>instrument</code> (e.g. NIFTY). "
                "Returns <code>TechnicalCommentaryResponse</code>: "
                "<code>instrument</code>, <code>commentary</code> (str), "
                "<code>signal_summary</code> (list of label/value/state). "
                "Auth: none. Schema: <code>src/rita/schemas/technical.py</code>.</td></tr>"
            )
            body_updated = (
                body_updated[:close_tbody]
                + new_row
                + "\n  "
                + body_updated[close_tbody:]
            )
            print("OK: Added technical-commentary endpoint row to Experience Layer table")

# ── 4. Add Technical Analysis section note ───────────────────────────────────
MARKER_TA = "rita-technical-analysis-phase01-2026-05-14"

TA_NOTE = (
    f"\n<!-- {MARKER_TA} -->\n"
    "<h3>RITA Dashboard &mdash; Technical Analysis Page (Phase 01, 2026-05-14)</h3>\n"
    "<p>A new <strong>Technical Analysis</strong> nav item has been added to the RITA dashboard "
    "(<code>rita.html</code>) under the PLAN menu group, immediately below Market Analysis. "
    "The section key is <code>technical-analysis</code> (DOM id: "
    "<code>sec-technical-analysis</code>).</p>\n"
    "<p><strong>Content:</strong></p>\n"
    "<ul>\n"
    "  <li><strong>Commentary panel</strong> (<code>div#ta-commentary</code>) &mdash; "
    "instrument-specific commentary and signal summary badges fetched from "
    "<code>GET /api/v1/experience/rita/technical-commentary</code>.</li>\n"
    "  <li><strong>Price &amp; Volume chart</strong> (<code>canvas#chart-ta-pv</code>).</li>\n"
    "  <li><strong>ATR% chart</strong> (<code>canvas#chart-ta-atr</code>) &mdash; "
    "<em>moved from Market Analysis</em>. The <code>chart-ms-atr</code> canvas was removed "
    "from <code>sec-market-signals</code>.</li>\n"
    "  <li><strong>RSI-14 chart</strong> (<code>canvas#chart-ta-rsi</code>) &mdash; "
    "<em>moved from Market Analysis</em>. The <code>chart-ms-rsi</code> canvas was removed "
    "from <code>sec-market-signals</code>.</li>\n"
    "</ul>\n"
    "<p><strong>JS module:</strong> <code>dashboard/js/rita/technical-analysis.js</code> "
    "exports <code>loadTechnicalAnalysis()</code>. The section is registered in "
    "<code>main.js</code> via <code>_sectionLoaders['technical-analysis']</code> and "
    "included in the <code>instrumentSections</code> Set so instrument tab switches "
    "reload the section data. No JWT required.</p>\n"
    "<p>Spec files updated: <code>Spec_RITA_App.md</code> (endpoint entry for "
    "<code>/api/v1/experience/rita/technical-commentary</code>) and "
    "<code>Spec_JS_Code.md</code> (<code>technical-analysis.js</code> row in the "
    "dashboard/js/rita/ module table).</p>\n"
)

if MARKER_TA in body_updated:
    print("NOTE: Technical Analysis section note already present — skipping")
else:
    # Insert before the Workflow h3, which follows the Experience Layer / nav-swap area
    WORKFLOW_H3 = "<h3>Workflow &mdash; <code>api/v1/workflow/</code></h3>"
    wf_idx = body_updated.find(WORKFLOW_H3)
    if wf_idx == -1:
        # Fallback: append before closing <hr /> after Experience Layer table
        body_updated = body_updated + TA_NOTE
        print("NOTE: Workflow h3 not found — Technical Analysis note appended to end of body")
    else:
        body_updated = body_updated[:wf_idx] + TA_NOTE + body_updated[wf_idx:]
        print("OK: Technical Analysis section note inserted before Workflow h3")

# ── 5. Bump version date ─────────────────────────────────────────────────────
for old_date in ("2026-05-11", "2026-05-08", "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        if old_date != "2026-05-14":
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-14",
                1,
            )
            print(f"OK: Version date bumped from {old_date} to 2026-05-14")
        else:
            print("NOTE: Date already at 2026-05-14")
        break

# ── 6. Push update ───────────────────────────────────────────────────────────
if body_updated == body:
    print("No changes made — page not updated")
else:
    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }
    result  = put(f"content/{PAGE_ID}", payload)
    new_ver = result["version"]["number"]
    url     = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
