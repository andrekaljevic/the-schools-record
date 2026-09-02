from __future__ import annotations

import hashlib
import re


PUBLIC_EXPERIENCE_MARKER = "/* schools-record-public-experience-v1 */"


PUBLIC_EXPERIENCE_CSS = rf"""
{PUBLIC_EXPERIENCE_MARKER}

.briefing-about {{
  display: grid;
  grid-template-columns: minmax(280px, .72fr) minmax(0, 1.28fr);
  gap: clamp(48px, 7vw, 104px);
  margin: 0;
  padding: 52px 2px 54px;
  border-bottom: 1px solid var(--line);
}}

.briefing-about-heading {{
  align-self: start;
  position: sticky;
  top: 104px;
}}

.briefing-about h2 {{
  max-width: 520px;
  margin: 0;
  color: var(--ink-strong);
  font-family: var(--font-display);
  font-size: clamp(38px, 4vw, 58px);
  font-weight: 500;
  line-height: 1.02;
  letter-spacing: -.044em;
  text-wrap: balance;
}}

.briefing-about-copy {{
  max-width: 760px;
  padding-top: 31px;
}}

.briefing-about-copy p {{
  margin: 0;
  color: #3f5559;
  font-size: 16px;
  line-height: 1.75;
}}

.briefing-about-copy p:first-child {{
  color: var(--ink);
  font-size: 19px;
  line-height: 1.67;
}}

.briefing-about-copy p + p {{
  margin-top: 18px;
}}

.evidence-tools {{
  grid-template-columns: minmax(260px, 1fr) 220px;
}}

.ledger-table-tools {{
  grid-template-columns: minmax(220px, 360px) 1fr auto;
}}

.comparison-section-label {{
  margin: 30px 0 10px;
  color: var(--cobalt-dark);
  font-size: 11px;
  font-weight: 780;
  line-height: 1.3;
  letter-spacing: .145em;
  text-transform: uppercase;
}}

@media (width <= 820px) {{
  .briefing-about {{
    grid-template-columns: 1fr;
    gap: 6px;
    margin: 0;
    padding: 38px 0 42px;
  }}

  .briefing-about-heading {{
    position: static;
  }}

  .briefing-about-copy {{
    max-width: 680px;
    padding-top: 20px;
  }}

  .evidence-tools {{
    grid-template-columns: 1fr;
  }}
}}

@media (width <= 520px) {{
  .briefing-about h2 {{
    font-size: 40px;
  }}

  .briefing-about-copy p:first-child {{
    font-size: 17px;
  }}

  .ledger-table-tools {{
    grid-template-columns: 1fr auto auto;
  }}
}}
"""


_COPY_REPLACEMENTS = (
    (
        "children:`The independent evidence record`",
        "children:`The Schools Record`",
        "homepage overline",
    ),
    (
        "children:[`Leading schools,`",
        "children:[`Independent school results,`",
        "homepage heading opening",
    ),
    (
        "`shown precisely.`",
        "`year by year.`",
        "homepage heading closing",
    ),
    (
        "children:`Examination results, university pathways and admissions evidence—kept on their original rulers, rounded to one decimal place and traceable to source.`",
        "children:`Historical examination results, university destinations and admissions figures for leading UK independent schools, brought together in clear charts and tables with notes on how each figure should be read.`",
        "homepage description",
    ),
    (
        "children:[`Compare same-ruler results `",
        "children:[`Compare schools `",
        "homepage comparison action",
    ),
    (
        "children:[`Search every record `",
        "children:[`Explore the records `",
        "homepage evidence action",
    ),
    (
        "{id:`briefing`,label:`Briefing`}",
        "{id:`briefing`,label:`Overview`}",
        "main overview navigation label",
    ),
    (
        "children:`Indexed observations`",
        "children:`Figures and records`",
        "homepage record inventory label",
    ),
    (
        "children:`Flagship schools`",
        "children:`Schools covered`",
        "homepage school inventory label",
    ),
    (
        "children:`2026 result rows`",
        "children:`2026 updates`",
        "homepage update inventory label",
    ),
    (
        "children:`Evidence snapshot`",
        "children:`Last reviewed`",
        "homepage date inventory label",
    ),
    (
        "children:`30 Aug 2026`",
        "children:`2 Sep 2026`",
        "evidence snapshot date",
    ),
    (
        "` Evidence snapshot · 2 Sep 2026`",
        "` Last reviewed · 2 Sep 2026`",
        "header review date",
    ),
    (
        "`The Schools Record — Longitudinal Evidence`",
        "`The Schools Record | UK Independent School Results`",
        "browser title",
    ),
    (
        "`Evidence`} | The Schools Record",
        "`Method & notes`} | The Schools Record",
        "method browser title",
    ),
    (
        "children:`The editorial contract`",
        "children:`Method`",
        "method overline",
    ),
    (
        "children:`Evidence before ranking.`",
        "children:`How the record works.`",
        "method heading",
    ),
    (
        "children:`Like with like`",
        "children:`Comparable figures only`",
        "comparison principle heading",
    ),
    (
        "children:`A level, GCSE, IB and Pre-U stay on separate qualification rulers. Cross-school comparison appears only where the metric, population and year basis match.`",
        "children:`Schools appear together only when the qualification, measure, pupil group and period match. A level, GCSE, IGCSE, IB and Pre-U results are never blended into a single scale.`",
        "comparison principle copy",
    ),
    (
        "children:`Exact means exact`",
        "children:`Keep the basis clear`",
        "published figure principle heading",
    ),
    (
        "children:`Individual and cumulative bands remain distinct: A*, A*–A, A*–B; grade 9, 9–8, 9–7; and every additional band actually published.`",
        "children:`Published figures remain as published. Any reconstructed or estimated value is labelled, rather than presented as an exact result.`",
        "published figure principle copy",
    ),
    (
        "children:`Trace the claim`",
        "children:`Show uncertainty plainly`",
        "source principle heading",
    ),
    (
        "children:`Stable observation identities, row-level sources, retained conflicts and explicit gaps turn the interface into an inspectable public record.`",
        "children:`Missing years stay blank. Corrections and differences between credible publications are explained in straightforward language. Private working documents are not available for download.`",
        "source principle copy",
    ),
    (
        "children:`Comparable-measure engine`",
        "children:`Compare schools`",
        "comparison overline",
    ),
    (
        "children:`One ruler. Every school it fits.`",
        "children:`See the schools on the same measure.`",
        "comparison heading",
    ),
    (
        "children:`Examination results, application outcomes and final destinations can now be compared without collapsing incompatible qualifications, cohorts or outcome stages.`",
        "children:`Choose an examination result or university measure. The chart and table update together, and include only figures that use the same definition, pupil group and time period.`",
        "comparison description",
    ),
    (
        "children:`Period & ruler`",
        "children:`Period and grading scale`",
        "comparison period label",
    ),
    (
        "children:`Comparability boundary`",
        "children:`Why some figures are left out`",
        "comparison boundary heading",
    ),
    (
        "children:`Change the selected schools or measure. Missing evidence is never plotted as zero.`",
        "children:`Change the selected schools or measure. A missing result is never shown as zero.`",
        "comparison empty-state copy",
    ),
    (
        "children:`Change the selected schools or measure. Missing evidence is not plotted as zero.`",
        "children:`Change the selected schools or measure. A missing result is not shown as zero.`",
        "comparison compact empty-state copy",
    ),
    (
        "className:`compare-trend-details`,children:",
        "className:`compare-trend-details`,open:!0,children:",
        "default-open comparison chart",
    ),
    (
        "children:`View trend chart`",
        "children:`Interactive chart`",
        "comparison chart label",
    ),
    (
        "{id:`evidence`,label:`Evidence`}",
        "{id:`evidence`,label:`Method & notes`}",
        "main evidence navigation label",
    ),
    (
        "{id:`records`,label:`Records`,count:",
        "{id:`records`,label:`Figure notes`,count:",
        "evidence records navigation label",
    ),
    (
        "{id:`conflicts`,label:`Conflicts`,count:",
        "{id:`conflicts`,label:`Published differences`,count:",
        "evidence navigation label",
    ),
    (
        "children:`Evidence centre`",
        "children:`Method & notes`",
        "evidence overline",
    ),
    (
        "children:`The audit trail is a feature.`",
        "children:`How the figures are checked.`",
        "evidence heading",
    ),
    (
        "children:`Search every indexed source record, inspect corrections and conflicts, and move from a displayed claim back to its source.`",
        "children:`This section explains the method, records corrections and notes where published figures disagree. It does not provide access to the working archive behind the site.`",
        "evidence description",
    ),
    (
        "children:`indexed source records`",
        "children:`figures documented`",
        "evidence record statistic",
    ),
    (
        "children:`locked corrections`",
        "children:`corrections recorded`",
        "evidence correction statistic",
    ),
    (
        "children:`preserved conflicts`",
        "children:`published differences noted`",
        "evidence conflict statistic",
    ),
    (
        "placeholder:`School, year, subject, metric or record…`",
        "placeholder:`Search by school, year or measure…`",
        "evidence search prompt",
    ),
    (
        "children:`Inspect full record`",
        "children:`Show details`",
        "evidence detail action",
    ),
    (
        "children:`No matching evidence`",
        "children:`No matching records`",
        "empty evidence result",
    ),
    (
        "children:`Locked amendments`",
        "children:`Corrections`",
        "corrections overline",
    ),
    (
        "children:`Corrections remain visible.`",
        "children:`What changed, and why.`",
        "corrections heading",
    ),
    (
        "children:`The controlling value replaces the retired value in analysis, while the change and its reason stay in the public lineage.`",
        "children:`When a figure is corrected, the site uses the new value. The earlier value and the reason for the change are kept here.`",
        "corrections description",
    ),
    (
        "children:`Uncollapsed disagreements`",
        "children:`Published differences`",
        "source differences overline",
    ),
    (
        "children:`Conflict is data.`",
        "children:`When published figures do not agree.`",
        "source differences heading",
    ),
    (
        "children:`Where authoritative-looking sources disagree, the record preserves both claims and states the analytical treatment.`",
        "children:`Occasionally, two credible publications give different figures for the same year. Both values are noted here, together with the one used on the site and the reason for that choice.`",
        "source differences description",
    ),
    (
        "children:`Comparability protocol`",
        "children:`Method`",
        "evidence method overline",
    ),
    (
        "children:`Precision before ranking.`",
        "children:`How comparisons are made.`",
        "evidence method heading",
    ),
    (
        "children:`A result can be exact, interesting and still unsuitable for comparison. The record tests the outcome stage, cohort, qualification ruler, geography and time basis before a value is allowed onto a shared visual.`",
        "children:`Figures appear together only when they describe the same outcome, pupil group, qualification and period. A figure is left out if any of those points do not match.`",
        "evidence method description",
    ),
    (
        "children:`Outcome type is part of the metric`",
        "children:`Different outcomes stay separate`",
        "outcome method heading",
    ),
    (
        "children:`An offer is not an acceptance. A destination is not a UCAS-cycle result. A published “success rate” retains the source’s exact definition.`",
        "children:`An offer is not an acceptance, and an acceptance is not a final destination. Each measure keeps the definition used by its publisher.`",
        "outcome method copy",
    ),
    (
        "children:`Denominators do not travel`",
        "children:`Percentages keep their own denominator`",
        "denominator method heading",
    ),
    (
        "children:`A pupil count cannot be borrowed from another section, cohort or year to manufacture a rate.`",
        "children:`A pupil count from another section, cohort or year is never used to create a rate.`",
        "denominator method copy",
    ),
    (
        "children:`Intervals stay intervals`",
        "children:`Ranges stay as ranges`",
        "range method heading",
    ),
    (
        "children:`Oxford FOI values rounded down to multiples of five remain bounded ranges. Their midpoints are never plotted as observations.`",
        "children:`If a published count has been rounded, the site shows the possible range rather than inventing an exact figure.`",
        "range method copy",
    ),
    (
        "children:`Gaps are visible`",
        "children:`Missing years stay blank`",
        "gap method heading",
    ),
    (
        "children:`Missing 2010 and 2012 Cambridge school cycles are not interpolated. Provisional 2025 school rows are excluded from default trends.`",
        "children:`The site does not interpolate missing results, and provisional figures are not mixed into the default historical series.`",
        "gap method copy",
    ),
    (
        "children:`Controlling source families`",
        "children:`Published material used`",
        "source register heading",
    ),
    (
        "children:`Oxbridge evidence family`",
        "children:`Oxbridge publications`",
        "source register footer",
    ),
    (
        "{all:`All evidence`,figures:`Figures Bible`,oxbridge:`Oxbridge`,us:`US universities`}",
        "{all:`All records`,figures:`School results and destinations`,oxbridge:`Oxbridge`,us:`US universities`}",
        "evidence corpus labels",
    ),
    (
        "children:`Displayed values retain the source’s outcome type, unit and qualification ruler. A dash means not reported, never zero.`",
        "children:`Figures keep the outcome, unit and grading scale used by the publisher. A dash means not reported, never zero.`",
        "school table guidance",
    ),
    (
        '"aria-label":`Exact qualification ruler`',
        '"aria-label":`Published grading scale`',
        "school grading-scale aria label",
    ),
    (
        "children:`Exact qualification ruler`",
        "children:`Published grading scale`",
        "drawer grading-scale label",
    ),
    (
        "children:`Exact results ruler`",
        "children:`Published grading scale`",
        "school grading-scale heading",
    ),
    (
        "children:`No modern same-ruler series is encoded.`",
        "children:`No directly comparable modern series is available.`",
        "school comparison empty-state copy",
    ),
    (
        "children:`No table-ready series in the held corpus`",
        "children:`No suitable table is available`",
        "school table empty-state copy",
    ),
    (
        "children:`Evidence corpus`",
        "children:`Record type`",
        "evidence filter label",
    ),
    (
        "children:`Evidence status`",
        "children:`Source status`",
        "source status label",
    ),
    (
        "children:`Published process, with the boundary visible`",
        "children:`Published process and known limits`",
        "admissions process heading",
    ),
    (
        "children:`Qualification scales and outcome types stay on separate published rulers. CAG/TAG rows are visibly marked.`",
        "children:`Different qualifications and outcome types remain separate. Teacher-assessed results from 2020 and 2021 are clearly marked.`",
        "school table method copy",
    ),
    (
        "children:`Row-level evidence`",
        "children:`Figure notes`",
        "row notes label",
    ),
    (
        "children:`School admissions · separate evidence domain`",
        "children:`School admissions · separate section`",
        "admissions section label",
    ),
    (
        "children:`Search evidence`",
        "children:`Search records`",
        "record search label",
    ),
    (
        "children:`The Oxford and Cambridge source corpus is loaded only when this domain is requested.`",
        "children:`Oxford and Cambridge records load when this section is opened.`",
        "Oxbridge loading guidance",
    ),
    (
        "children:`The detailed US corpus is loaded only when this series is requested.`",
        "children:`Detailed US university records load when this series is opened.`",
        "US loading guidance",
    ),
    (
        "children:`Try a school name, a different year or a broader corpus.`",
        "children:`Try a school name, a different year or a broader search.`",
        "record search empty-state guidance",
    ),
    (
        "children:`View data table and trace evidence`",
        "children:`View table and figure notes`",
        "table disclosure label",
    ),
    (
        "children:`Your place is safe. Retry the exact source corpus without leaving this view.`",
        "children:`Your place is saved. Retry the records without leaving this view.`",
        "record load error guidance",
    ),
    (
        "children:`Your selected series is preserved. Retry the source corpus without leaving this view.`",
        "children:`Your selected series is saved. Retry the records without leaving this view.`",
        "series load error guidance",
    ),
)


_BUTTON_START = re.compile(
    r",\(0,[A-Za-z_$][A-Za-z0-9_$]*\.jsxs\)\(\`button\`,\{"
)
_LEDGER_DOWNLOAD_HANDLER = re.compile(
    r",(?P<handler>[A-Za-z_$][A-Za-z0-9_$]*)=\(\)=>\{let t="
    r"\[\`Qualification ruler\`,\`Grade scale\`,\`Denominator\`,"
    r"\`Observation ID\`,\`Record ID\`,\`Dataset ID\`,\`Published basis\`,"
    r"\`Source references\`,\`Source URL\`\],"
    r".*?\.download=\`\$\{e\.dataset_id\}\.csv\`.*?"
    r"URL\.revokeObjectURL\([A-Za-z_$][A-Za-z0-9_$]*\),0\)\},"
    r"(?P<next>[A-Za-z_$][A-Za-z0-9_$]*=\(t,n\)=>\{)",
    re.DOTALL,
)
_PRIVATE_DOCUMENT_URL = re.compile(r"https://(?:drive|docs)\.google\.com/[^\s\`\"]+")
_PRIVATE_DOCUMENT_ID = re.compile(
    r"(?:/d/|[?&]id=)([A-Za-z0-9_-]{16,})"
)
_JS_PRIVATE_URL_VALUE = re.compile(
    r"(?P<prefix>\b(?:url|source_url|sourceUrl):)"
    r"\`(?P<url>https://(?:drive|docs)\.google\.com/[^\`]*)\`"
)
_JSON_PRIVATE_URL_VALUE = re.compile(
    r'(?P<prefix>"(?:url|source_url|sourceUrl)":)'
    r'"(?P<url>https://(?:drive|docs)\.google\.com/[^"]*)"'
)
_RELEASE_BOARD_START = re.compile(
    r",\(0,(?P<jsx>[A-Za-z_$][A-Za-z0-9_$]*)\.jsxs\)"
    r"\(\`section\`,\{className:\`release-board\`"
)
_COMPARISON_TABLE_START = re.compile(
    r",\(0,(?P<jsx>[A-Za-z_$][A-Za-z0-9_$]*)\.jsx\)"
    r"\(\`div\`,\{className:\`comparison-matrix-scroll\`"
)
_COMPARISON_CHART_START = re.compile(
    r",\(0,(?P<jsx>[A-Za-z_$][A-Za-z0-9_$]*)\.jsxs\)"
    r"\(\`details\`,\{className:\`compare-trend-details\`,open:!0,children:"
)
_COMPARISON_NOTE_START = re.compile(
    r",\(0,(?P<jsx>[A-Za-z_$][A-Za-z0-9_$]*)\.jsxs\)"
    r"\(\`aside\`,\{className:\`comparison-note\`"
)


def _replace_once(source: str, before: str, after: str, label: str) -> str:
    if source.count(before) != 1:
        raise RuntimeError(
            f"Unable to apply public experience update for {label}: "
            "expected one bundle match"
        )
    return source.replace(before, after, 1)


def _remove_button_with_label(source: str, label: str, expected: int) -> str:
    for _ in range(expected):
        label_index = source.find(label)
        if label_index < 0:
            raise RuntimeError(
                f"Unable to remove public download control {label}: "
                "expected another matching label"
            )

        starts = list(_BUTTON_START.finditer(source, 0, label_index))
        if not starts:
            raise RuntimeError(
                f"Unable to remove public download control {label}: "
                "button start was not found"
            )

        start_match = starts[-1]
        label_end = label_index + len(label)
        if not source.startswith("]})", label_end):
            raise RuntimeError(
                f"Unable to remove public download control {label}: "
                "label was not the final button child"
            )
        end = label_end + len("]})")
        source = source[: start_match.start()] + source[end:]

    if label in source:
        raise RuntimeError(
            f"Unable to remove public download control {label}: "
            "unexpected additional matching labels"
        )
    return source


def _remove_ledger_download_handler(source: str) -> str:
    def keep_next_assignment(match: re.Match[str]) -> str:
        return f",{match.group('next')}"

    source, count = _LEDGER_DOWNLOAD_HANDLER.subn(keep_next_assignment, source)
    if count != 1:
        raise RuntimeError(
            "Unable to remove the school-table download handler: "
            f"expected one bundle match, found {count}"
        )
    return source


def _inject_homepage_explanation(source: str) -> str:
    matches = list(_RELEASE_BOARD_START.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(
            "Unable to add the homepage explanation: expected one release-board match"
        )

    match = matches[0]
    jsx = match.group("jsx")
    explanation = (
        f",(0,{jsx}.jsxs)(`section`,{{className:`briefing-about`,"
        '"aria-labelledby":`about-record-title`,children:['
        f"(0,{jsx}.jsxs)(`div`,{{className:`briefing-about-heading`,children:["
        f"(0,{jsx}.jsx)(`p`,{{className:`overline`,children:`About the site`}}),"
        f"(0,{jsx}.jsx)(`h2`,{{id:`about-record-title`,children:`A clearer record of school results.`}})]}}),"
        f"(0,{jsx}.jsxs)(`div`,{{className:`briefing-about-copy`,children:["
        f"(0,{jsx}.jsx)(`p`,{{children:`The Schools Record is an independent, year-by-year guide to examination results, university destinations and admissions figures at leading UK independent schools. It brings together material that is often scattered across school reports, archived webpages, public data releases and contemporary publications.`}}),"
        f"(0,{jsx}.jsx)(`p`,{{children:`The current edition covers Eton College, Westminster School, King’s College School Wimbledon, St Paul’s School, St Paul’s Girls’ School, Wycombe Abbey and Winchester College. Further schools are added when there is enough reliable evidence to build a useful historical record.`}}),"
        f"(0,{jsx}.jsx)(`p`,{{children:`A level, GCSE, IGCSE, IB and Pre-U results remain separate. Offers, admissions and final destinations remain separate too. Published figures keep their original definitions, reconstructed estimates are labelled, and missing years stay blank. Comparable views show both an interactive chart and the exact table.`}})]}})]}})"
    )
    return source[: match.start()] + explanation + source[match.start() :]


def _inject_comparison_table_label(source: str) -> str:
    matches = list(_COMPARISON_TABLE_START.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(
            "Unable to label the comparison table: expected one table match"
        )

    match = matches[0]
    jsx = match.group("jsx")
    label = (
        f",(0,{jsx}.jsx)(`p`,{{className:`comparison-section-label`,"
        "children:`Table`})"
    )
    return source[: match.start()] + label + source[match.start() :]


def _move_comparison_chart_before_table(source: str) -> str:
    table_matches = list(_COMPARISON_TABLE_START.finditer(source))
    chart_matches = list(_COMPARISON_CHART_START.finditer(source))
    note_matches = list(_COMPARISON_NOTE_START.finditer(source))
    if len(table_matches) != 1 or len(chart_matches) != 1 or len(note_matches) != 1:
        raise RuntimeError(
            "Unable to place the comparison chart: expected one table, chart and note"
        )

    table_start = table_matches[0].start()
    chart_start = chart_matches[0].start()
    note_start = note_matches[0].start()
    if not table_start < chart_start < note_start:
        raise RuntimeError("Unable to place the comparison chart: unexpected bundle order")

    chart = source[chart_start:note_start]
    source = source[:chart_start] + source[note_start:]
    return source[:table_start] + chart + source[table_start:]


def _redact_private_document_links(source: str) -> str:
    private_ids: set[str] = set()
    contains_private_domain = (
        "drive.google.com" in source or "docs.google.com" in source
    )

    def record_private_id(url: str) -> None:
        identifier = _PRIVATE_DOCUMENT_ID.search(url)
        if identifier:
            private_ids.add(identifier.group(1))

    def replace_value(match: re.Match[str]) -> str:
        record_private_id(match.group("url"))
        return f'{match.group("prefix")}null'

    source, js_redacted = _JS_PRIVATE_URL_VALUE.subn(replace_value, source)
    source, json_redacted = _JSON_PRIVATE_URL_VALUE.subn(replace_value, source)
    if js_redacted + json_redacted == 0:
        if contains_private_domain:
            raise RuntimeError(
                "Unable to protect private source documents: "
                "Drive or Docs links were not in recognised source fields"
            )
        return source

    for identifier in private_ids:
        alias = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16]
        source = source.replace(identifier, f"private-source-{alias}")

    if "drive.google.com" in source or "docs.google.com" in source:
        raise RuntimeError("Unable to protect every private Drive or Docs source link")
    return source


def apply_public_experience_updates(css: str, javascript: str) -> tuple[str, str]:
    """Apply the reviewed public-site copy, comparison, and access updates."""

    css_has_marker = PUBLIC_EXPERIENCE_MARKER in css
    js_has_marker = PUBLIC_EXPERIENCE_MARKER in javascript
    if css_has_marker and js_has_marker:
        return css, javascript
    if css_has_marker or js_has_marker:
        raise RuntimeError("Public experience update is only partially applied")

    required_css = (".briefing-hero{", ".evidence-tools{", ".ledger-table-tools{")
    missing_css = [selector for selector in required_css if selector not in css]
    if missing_css:
        raise RuntimeError(
            "Unable to apply public experience update: missing bundle selectors "
            + ", ".join(missing_css)
        )

    for before, after, label in _COPY_REPLACEMENTS:
        javascript = _replace_once(javascript, before, after, label)

    javascript = _inject_homepage_explanation(javascript)
    javascript = _move_comparison_chart_before_table(javascript)
    javascript = _inject_comparison_table_label(javascript)
    javascript = _remove_button_with_label(javascript, "` Download index`", 1)
    javascript = _remove_button_with_label(javascript, "` CSV`", 2)
    javascript = _remove_ledger_download_handler(javascript)
    javascript = _redact_private_document_links(javascript)

    javascript = f"{PUBLIC_EXPERIENCE_MARKER}\n{javascript}"
    css = f"{css}\n{PUBLIC_EXPERIENCE_CSS.strip()}\n"
    return css, javascript
