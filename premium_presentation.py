from __future__ import annotations


PREMIUM_PRESENTATION_MARKER = "/* schools-record-premium-presentation-v1 */"


PREMIUM_PRESENTATION_CSS = rf"""
{PREMIUM_PRESENTATION_MARKER}

/*
 * The Schools Record presentation layer
 * British institutional modernism: warm archival paper, precise rules,
 * restrained brass and teal, and highly legible data surfaces.
 */
:root {{
  --canvas: #f4f1ea;
  --canvas-deep: #e9e4da;
  --surface: #fffefa;
  --surface-raised: #ffffff;
  --surface-soft: #ece8df;
  --ink: #112126;
  --ink-strong: #08171b;
  --ink-soft: #33484c;
  --muted: #607175;
  --line: #d8d2c6;
  --line-strong: #aaa497;
  --cobalt: #0a6873;
  --cobalt-dark: #07515a;
  --cobalt-soft: #e3f0ef;
  --green: #087860;
  --amber: #96600a;
  --red: #ad4137;
  --brass: #8d7348;
  --brass-soft: #eee5d5;
  --font-display: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --font-ui: "Avenir Next", Avenir, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --radius-panel: 14px;
  --radius-control: 8px;
  --shadow: 0 1px 1px rgba(8, 23, 27, .04), 0 16px 46px rgba(27, 40, 43, .075);
  --shadow-raised: 0 1px 1px rgba(8, 23, 27, .05), 0 9px 24px rgba(27, 40, 43, .055), 0 28px 70px rgba(27, 40, 43, .07);
}}

html {{
  background: var(--canvas);
  color-scheme: light;
  scroll-padding-top: 90px;
}}

body {{
  background:
    radial-gradient(circle at 8% -8%, rgba(141, 115, 72, .085), transparent 33rem),
    linear-gradient(180deg, rgba(255, 255, 255, .38), transparent 29rem),
    var(--canvas);
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: 16px;
  line-height: 1.58;
  letter-spacing: -.006em;
  font-kerning: normal;
  font-feature-settings: "kern" 1, "liga" 1;
}}

::selection {{
  background: #c8e1df;
  color: var(--ink-strong);
}}

:where(a, button, input, select, summary):focus-visible {{
  outline: 3px solid rgba(10, 104, 115, .7);
  outline-offset: 3px;
}}

button, input, select {{
  font: inherit;
}}

.overline {{
  display: flex;
  align-items: center;
  gap: 11px;
  color: var(--cobalt-dark);
  margin-bottom: 16px;
  text-decoration: none;
  letter-spacing: .145em;
  font-size: 11px;
  line-height: 1.3;
}}

.overline::before {{
  content: "";
  width: 34px;
  height: 1px;
  flex: 0 0 34px;
  background: linear-gradient(90deg, var(--brass), var(--cobalt));
}}

.site-header {{
  height: 72px;
  grid-template-columns: minmax(210px, 1fr) auto minmax(210px, 1fr);
  gap: 28px;
  padding-inline: max(28px, calc(50vw - 704px));
  border-bottom: 1px solid rgba(170, 164, 151, .62);
  background: rgba(255, 254, 250, .9);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .88), 0 10px 36px rgba(17, 33, 38, .045);
}}

.site-header::before {{
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--cobalt-dark) 0 12%, var(--brass) 12% 21%, transparent 21% 100%);
  opacity: .86;
}}

.wordmark {{
  gap: 12px;
  min-height: 48px;
}}

.wordmark > span {{
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, .18);
  border-radius: 6px;
  background: linear-gradient(145deg, #183039, #0a1b20);
  box-shadow: inset 0 0 0 1px rgba(141, 115, 72, .38), 0 5px 15px rgba(8, 23, 27, .13);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
}}

.wordmark strong {{
  color: var(--ink-strong);
  font-size: 15px;
  letter-spacing: -.025em;
}}

.site-header nav {{
  gap: 3px;
}}

.site-header nav a {{
  min-width: 88px;
  padding-inline: 16px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 690;
  transition: color .18s ease, background-color .18s ease;
}}

.site-header nav a::after {{
  left: 16px;
  right: 16px;
  bottom: 7px;
  height: 2px;
  background: linear-gradient(90deg, var(--brass), var(--cobalt));
}}

.site-header nav a.active {{
  color: var(--ink-strong);
}}

.snapshot-mark {{
  min-height: 32px;
  width: fit-content;
  justify-self: end;
  padding: 0 11px;
  border: 1px solid rgba(8, 120, 96, .18);
  border-radius: 999px;
  background: rgba(227, 240, 239, .62);
  color: #41605f;
  font-size: 11px;
  letter-spacing: .015em;
}}

.snapshot-mark i {{
  width: 6px;
  height: 6px;
  box-shadow: 0 0 0 4px rgba(8, 120, 96, .11);
}}

.briefing-view {{
  max-width: 1440px;
  min-height: calc(100svh - 72px);
  padding: 64px 32px 124px;
}}

.compare-view, .school-view, .evidence-view {{
  max-width: 1376px;
  min-height: calc(100svh - 72px);
  padding: 78px 32px 112px;
}}

.briefing-hero {{
  min-height: 414px;
  grid-template-columns: minmax(0, 1.42fr) minmax(360px, .58fr);
  gap: clamp(58px, 6vw, 96px);
  align-items: center;
  padding-bottom: 34px;
  border-bottom-color: rgba(170, 164, 151, .84);
}}

.briefing-hero > div:first-child {{
  max-width: 900px;
}}

.briefing-hero h1,
.release-board-heading h2,
.briefing-principles h2,
.view-intro h1,
.evidence-hero h1,
.record-masthead h1,
.record-evidence-header h2,
.trace-header h2 {{
  font-family: var(--font-display);
  color: var(--ink-strong);
  text-wrap: balance;
}}

.briefing-hero h1 {{
  max-width: 830px;
  font-size: clamp(60px, 6.3vw, 91px);
  font-weight: 500;
  line-height: .92;
  letter-spacing: -.058em;
}}

.briefing-deck {{
  max-width: 700px;
  margin-top: 28px;
  color: #506367;
  font-size: 18px;
  line-height: 1.68;
}}

.briefing-actions {{
  gap: 11px;
  margin-top: 30px;
}}

.briefing-actions a {{
  min-height: 50px;
  padding-inline: 19px;
  border-color: var(--line-strong);
  border-radius: var(--radius-control);
  background: rgba(255, 254, 250, .62);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .75);
  color: var(--cobalt-dark);
  font-size: 13px;
  font-weight: 760;
  transition: transform .18s ease, box-shadow .18s ease, background-color .18s ease, border-color .18s ease;
}}

.briefing-actions a.primary-action {{
  border-color: var(--ink-strong);
  background: linear-gradient(145deg, #19323a, #0a1b20);
  box-shadow: inset 0 1px rgba(255, 255, 255, .1), 0 8px 20px rgba(8, 23, 27, .14);
}}

.briefing-inventory {{
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(170, 164, 151, .88);
  border-radius: var(--radius-panel);
  background: rgba(255, 254, 250, .78);
  box-shadow: var(--shadow-raised);
}}

.briefing-inventory::before {{
  content: "";
  position: absolute;
  z-index: 2;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, var(--cobalt-dark), var(--brass) 52%, rgba(141, 115, 72, .14));
}}

.briefing-inventory div {{
  min-height: 124px;
  border-color: var(--line);
  background: rgba(255, 254, 250, .74);
  padding: 20px;
}}

.briefing-inventory dt {{
  color: #68777a;
  text-transform: uppercase;
  letter-spacing: .075em;
  font-size: 10px;
  font-weight: 770;
}}

.briefing-inventory dd {{
  color: var(--ink-strong);
  font-family: var(--font-display);
  font-size: clamp(28px, 2.6vw, 38px);
  font-weight: 600;
  letter-spacing: -.04em;
}}

.release-board {{
  padding-top: 68px;
}}

.release-board-heading {{
  align-items: end;
}}

.release-board-heading h2,
.briefing-principles h2 {{
  font-size: clamp(40px, 4vw, 57px);
  line-height: 1.02;
  letter-spacing: -.045em;
}}

.release-board-heading > div:first-child > p:last-child {{
  margin-top: 16px;
  color: #58696c;
  font-size: 14px;
  line-height: 1.68;
}}

.release-summary {{
  gap: 8px;
}}

.release-summary span {{
  min-height: 34px;
  padding-inline: 11px;
  border: 1px solid rgba(170, 164, 151, .4);
  background: rgba(236, 232, 223, .72);
  color: #596a6d;
  font-size: 10px;
  letter-spacing: .025em;
}}

.release-summary span.complete {{
  border-color: rgba(8, 120, 96, .18);
  background: #e5f3ee;
}}

.release-summary span.partial {{
  border-color: rgba(150, 96, 10, .18);
  background: #fbefd9;
}}

.release-table-shell {{
  margin-top: 27px;
  overflow: auto;
  border: 1px solid rgba(170, 164, 151, .9);
  border-radius: var(--radius-panel);
  background: var(--surface);
  box-shadow: var(--shadow);
}}

.release-table thead th {{
  height: 62px;
  border-color: var(--line);
  background: linear-gradient(180deg, #efede6, #e8e4da);
  color: #3c5054;
  padding-inline: 17px;
}}

.release-table thead span {{
  font-size: 12px;
  letter-spacing: -.005em;
}}

.release-table thead small {{
  font-size: 10px;
}}

.release-table tbody > tr > th {{
  background: #faf8f2;
  padding: 18px;
  font-size: 14px;
}}

.release-cell {{
  min-height: 150px;
  gap: 12px;
  padding: 16px 17px 13px;
}}

.release-cell dd {{
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
}}

.release-state {{
  letter-spacing: .03em;
}}

.briefing-principles {{
  gap: clamp(42px, 6vw, 78px);
  margin-top: 92px;
  padding-top: 54px;
}}

.principle-grid {{
  overflow: hidden;
  border: 1px solid rgba(170, 164, 151, .86);
  border-radius: var(--radius-panel);
  background: var(--surface);
  box-shadow: var(--shadow);
}}

.principle-grid article {{
  min-height: 266px;
  padding: 23px;
  border-color: var(--line);
  background: rgba(255, 254, 250, .84);
}}

.principle-grid article::before {{
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--brass), transparent 72%);
  opacity: .62;
}}

.principle-grid article > span {{
  letter-spacing: .08em;
}}

.principle-grid svg {{
  width: 21px;
  height: 21px;
  box-sizing: content-box;
  margin-top: 42px;
  padding: 9px;
  border: 1px solid rgba(10, 104, 115, .14);
  border-radius: 8px;
  background: var(--cobalt-soft);
}}

.principle-grid h3 {{
  margin-top: 14px;
  color: var(--ink-strong);
  font-size: 16px;
}}

.principle-grid p {{
  font-size: 12px;
  line-height: 1.68;
}}

.view-intro {{
  max-width: 820px;
}}

.view-intro h1 {{
  font-size: clamp(48px, 5vw, 72px);
  line-height: .98;
  letter-spacing: -.05em;
}}

.view-intro > p:last-child {{
  max-width: 700px;
  margin-top: 21px;
  color: #536669;
  font-size: 17px;
  line-height: 1.66;
}}

.comparison-toolbar,
.comparison-canvas {{
  border-color: rgba(170, 164, 151, .68);
  background: rgba(255, 254, 250, .9);
  box-shadow: var(--shadow);
}}

.comparison-toolbar {{
  margin-top: 46px;
  padding: 18px;
  border-radius: var(--radius-panel);
}}

.comparison-toolbar select,
.evidence-tools input,
.evidence-tools select {{
  border-color: var(--line-strong);
  border-radius: var(--radius-control);
  background-color: #fff;
  box-shadow: inset 0 1px 2px rgba(8, 23, 27, .035);
}}

.comparison-toolbar select:hover,
.evidence-tools input:hover,
.evidence-tools select:hover {{
  border-color: #7f8e8d;
}}

.comparison-canvas {{
  border-radius: var(--radius-panel);
  box-shadow: var(--shadow-raised);
}}

.comparison-domain-switch,
.evidence-nav {{
  gap: 28px;
  border-bottom-color: var(--line-strong);
}}

.comparison-domain-switch button,
.evidence-nav button {{
  min-height: 54px;
  font-size: 13px;
}}

.comparison-domain-switch button::after,
.evidence-nav button::after {{
  height: 3px;
  background: linear-gradient(90deg, var(--brass), var(--cobalt));
}}

.metric-contract {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(250, 248, 242, .68);
}}

.metric-contract > div {{
  padding: 19px 21px;
}}

.comparison-matrix-scroll {{
  overflow: auto;
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  background: var(--surface);
}}

.comparison-matrix thead th,
.ledger-table thead th {{
  background: linear-gradient(180deg, #efede6, #e6e2d9);
  color: #3b5054;
  box-shadow: inset 0 -1px rgba(170, 164, 151, .34);
}}

.comparison-matrix tbody th,
.comparison-matrix tbody td {{
  transition: background-color .14s ease;
}}

.comparison-matrix tbody tr:hover th,
.comparison-matrix tbody tr:hover td {{
  background: #edf4f1;
}}

.chart-grid {{
  stroke: #dedbd2;
}}

.chart-tick,
.chart-axis-title {{
  fill: #66777a;
}}

.chart-tooltip {{
  border-color: rgba(170, 164, 151, .82);
  background: rgba(255, 254, 250, .97);
  border-radius: 10px;
  box-shadow: var(--shadow-raised);
}}

.evidence-hero {{
  gap: 72px;
}}

.evidence-hero h1 {{
  font-size: clamp(50px, 5.4vw, 78px);
  line-height: .98;
  letter-spacing: -.05em;
}}

.evidence-boundary {{
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(141, 115, 72, .38);
  border-radius: var(--radius-panel);
  background: linear-gradient(145deg, #183139, #0b1d22);
  box-shadow: var(--shadow-raised);
}}

.evidence-boundary::before {{
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, #b99b68, #5fa0a5);
}}

.evidence-totals {{
  border-color: rgba(170, 164, 151, .7);
  border-radius: 12px;
  box-shadow: var(--shadow);
}}

.evidence-totals strong {{
  font-family: var(--font-display);
  font-weight: 600;
}}

.evidence-list {{
  display: grid;
  gap: 12px;
  margin-top: 6px;
  border-top: 0;
}}

.evidence-record {{
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(255, 254, 250, .88);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .72), 0 8px 26px rgba(27, 40, 43, .035);
  padding: 21px;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}}

.record-mark > span {{
  border: 1px solid rgba(170, 164, 151, .3);
  border-radius: 999px;
}}

.record-main h2 {{
  color: var(--ink-strong);
  font-size: 18px;
}}

.record-sources a {{
  border-radius: 7px;
}}

.record-view {{
  padding-top: 28px;
}}

.record-masthead {{
  position: relative;
  overflow: hidden;
  min-height: 246px;
  align-items: center;
  padding: clamp(28px, 4vw, 52px);
  border: 1px solid rgba(170, 164, 151, .74);
  border-radius: var(--radius-panel);
  background:
    radial-gradient(circle at 79% 16%, rgba(10, 104, 115, .075), transparent 25rem),
    linear-gradient(135deg, rgba(255, 255, 255, .92), rgba(248, 245, 237, .9));
  box-shadow: var(--shadow-raised);
}}

.record-masthead::before {{
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, var(--cobalt-dark), var(--brass) 52%, transparent 88%);
}}

.record-masthead h1 {{
  font-size: clamp(48px, 4.7vw, 66px);
  line-height: .98;
  letter-spacing: -.05em;
}}

.record-heading > p:last-child {{
  margin-top: 14px;
  color: #536669;
  font-size: 14px;
  line-height: 1.62;
}}

.record-masthead-illustrated {{
  min-height: 410px;
  grid-template-columns: minmax(340px, 1fr) minmax(255px, 350px) minmax(220px, auto);
  gap: clamp(28px, 4vw, 62px);
}}

.school-record-portrait {{
  position: relative;
  height: 330px;
  margin: 0;
  display: grid;
  place-items: center;
}}

.school-record-portrait::after {{
  content: "";
  position: absolute;
  inset: auto 8% 4% 8%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(141, 115, 72, .48), transparent);
}}

.school-record-portrait img {{
  filter: sepia(.08) contrast(.97) saturate(.78);
  opacity: .94;
}}

.record-coverage {{
  min-width: 245px;
  gap: 5px;
  padding: 17px 18px;
  border: 1px solid rgba(10, 104, 115, .22);
  border-left: 3px solid var(--cobalt);
  border-radius: 9px;
  background: rgba(255, 255, 255, .66);
  box-shadow: 0 8px 24px rgba(27, 40, 43, .04);
}}

.record-coverage strong {{
  color: var(--ink-strong);
  font-family: var(--font-display);
  font-size: 27px;
  font-weight: 600;
}}

.record-school-rail {{
  overflow: hidden;
  margin-top: 20px;
  border: 1px solid rgba(170, 164, 151, .78);
  border-radius: 10px;
  background: rgba(255, 254, 250, .7);
  box-shadow: 0 7px 24px rgba(27, 40, 43, .03);
}}

.record-school-rail a {{
  min-height: 52px;
  transition: color .15s ease, background-color .15s ease;
}}

.record-school-rail a.active {{
  background: #fff;
  box-shadow: inset 0 -3px var(--cobalt), 0 3px 12px rgba(27, 40, 43, .045);
}}

.record-domain-tabs {{
  overflow: hidden;
  margin-top: 12px;
  border: 1px solid rgba(170, 164, 151, .72);
  border-radius: 10px;
  background: rgba(255, 254, 250, .65);
}}

.record-domain-tabs button {{
  min-height: 62px;
  padding-inline: 18px;
}}

.record-domain-tabs button.active {{
  background: #fff;
}}

.record-domain-tabs button::after {{
  left: 17px;
  right: 17px;
  background: linear-gradient(90deg, var(--brass), var(--cobalt));
}}

.record-workspace {{
  grid-template-columns: 252px minmax(0, 1fr);
  gap: 38px;
  margin-top: 24px;
}}

.series-index {{
  overflow: hidden;
  top: 96px;
  border: 1px solid rgba(170, 164, 151, .72);
  border-radius: 10px;
  background: rgba(255, 254, 250, .72);
  box-shadow: 0 9px 28px rgba(27, 40, 43, .04);
}}

.series-index > p {{
  padding: 15px 14px;
  border-bottom: 1px solid var(--line);
  background: #efebe2;
  color: #647477;
  font-size: 10px;
  letter-spacing: .11em;
}}

.series-index > a {{
  min-height: 66px;
  padding: 12px 14px;
  border-top: 0;
  border-bottom: 1px solid var(--line);
}}

.series-index > a:last-child {{
  border-bottom: 0;
}}

.series-index > a.active {{
  border-left: 3px solid var(--cobalt);
  background: #fff;
  box-shadow: inset 0 1px rgba(255, 255, 255, .9), 0 6px 18px rgba(27, 40, 43, .035);
}}

.ledger-header {{
  gap: 38px;
  padding: 4px 3px 24px;
}}

.ledger-header h2 {{
  color: var(--ink-strong);
  font-family: var(--font-display);
  font-size: clamp(30px, 2.8vw, 39px);
  font-weight: 600;
  letter-spacing: -.04em;
}}

.ledger-header > div:first-child > p:last-child {{
  color: #56696c;
}}

.ledger-provenance {{
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 254, 250, .7);
}}

.ledger-provenance code {{
  font-family: var(--font-mono);
}}

.ruler-contract {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px 10px 0 0;
  background: linear-gradient(135deg, #f8f5ee, #f0ece3);
}}

.ruler-contract > strong {{
  color: var(--ink-strong);
  font-family: var(--font-display);
}}

.result-publication-strip,
.result-candidate-strip,
.result-highlight-strip {{
  border-left: 1px solid var(--line);
  border-right: 1px solid var(--line);
}}

.result-publication-strip {{
  background: #edf3ef;
}}

.result-candidate-strip {{
  background: #e3efec;
}}

.result-highlight-strip {{
  background: #f5f1e8;
}}

.result-candidate-strip strong,
.result-highlight-strip strong {{
  color: var(--ink-strong);
  font-family: var(--font-display);
  font-weight: 600;
}}

.ledger-table-tools {{
  min-height: 54px;
  border: 1px solid var(--line-strong);
  border-bottom: 0;
  background: rgba(255, 254, 250, .92);
}}

.ledger-table-tools label {{
  height: 52px;
}}

.ledger-table-tools label:focus-within {{
  outline: 3px solid rgba(10, 104, 115, .7);
  outline-offset: -3px;
  background: #fff;
}}

.ledger-table-scroll {{
  max-height: 700px;
  overflow: auto;
  border: 1px solid var(--line-strong);
  border-radius: 0 0 11px 11px;
  background: var(--surface);
  box-shadow: var(--shadow);
}}

.ledger-table {{
  font-size: 14px;
}}

.ledger-table th,
.ledger-table td {{
  height: 49px;
  padding: 10px 15px;
  border-color: #ddd8cd;
}}

.ledger-table thead th {{
  font-size: 12px;
  letter-spacing: .005em;
}}

.ledger-table tbody th {{
  color: var(--ink-strong);
  font-size: 13px;
}}

.ledger-table tbody td {{
  color: #344a4e;
}}

.ledger-table tbody tr:nth-child(2n) th,
.ledger-table tbody tr:nth-child(2n) td {{
  background: #faf8f3;
}}

.ledger-table tbody tr:hover th,
.ledger-table tbody tr:hover td {{
  background: #e8f1ee;
}}

.ledger-table .numeric-cell {{
  color: var(--ink-strong);
  font-variant-numeric: tabular-nums lining-nums;
}}

.ledger-table .inspect-cell button {{
  min-height: 38px;
  border: 1px solid rgba(10, 104, 115, .18);
  border-radius: 7px;
  background: rgba(227, 240, 239, .58);
}}

.ledger-notes {{
  margin-top: 24px;
  border-top-color: var(--line-strong);
}}

.ledger-notes > div {{
  padding-top: 18px;
}}

.result-mobile-cards article {{
  border-color: var(--line-strong);
  border-radius: 11px;
  box-shadow: var(--shadow);
}}

.result-mobile-cards header {{
  background: linear-gradient(180deg, #efede6, #e8e4da);
}}

.source-ref-list a,
.source-ref-list span,
.evidence-code {{
  border: 1px solid rgba(170, 164, 151, .4);
  border-radius: 6px;
  background: rgba(255, 254, 250, .84);
}}

.source-register > div {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--line);
  box-shadow: var(--shadow);
}}

.source-register a {{
  border-color: var(--line);
  background: var(--surface);
  transition: background-color .15s ease, color .15s ease;
}}

.record-evidence-sheet,
.trace-sheet {{
  border-left-color: rgba(170, 164, 151, .82) !important;
  background: var(--surface) !important;
  box-shadow: -22px 0 70px rgba(8, 23, 27, .22) !important;
}}

.record-evidence-header,
.trace-header {{
  background: linear-gradient(180deg, #faf8f2, #fffefa);
}}

.record-evidence-header h2,
.trace-header h2 {{
  color: var(--ink-strong);
  font-weight: 600;
}}

.record-evidence-body > aside,
.trace-caveat {{
  border: 1px solid var(--line);
  background: #f0ece3;
}}

.site-footer {{
  position: relative;
  min-height: 124px;
  border-top: 1px solid #172e34;
  background: linear-gradient(145deg, #132a31, #08171b);
  box-shadow: inset 0 1px rgba(255, 255, 255, .045);
}}

.site-footer::before {{
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--brass), #4d8589 38%, transparent 76%);
}}

.site-footer span {{
  color: #b4c1c3;
}}

.site-footer a {{
  color: #d7e7e7;
}}

@media (hover: hover) {{
  .site-header nav a:hover {{
    background: rgba(236, 232, 223, .58);
  }}

  .briefing-actions a:hover {{
    transform: translateY(-2px);
    border-color: #86897f;
    background: #fff;
    box-shadow: 0 8px 20px rgba(27, 40, 43, .08);
  }}

  .briefing-actions a.primary-action:hover {{
    border-color: var(--cobalt-dark);
    background: linear-gradient(145deg, #0f6c76, #084a52);
    box-shadow: 0 10px 24px rgba(7, 81, 90, .2);
  }}

  .evidence-record:hover {{
    transform: translateY(-1px);
    border-color: #aaa497;
    box-shadow: 0 14px 35px rgba(27, 40, 43, .07);
  }}

  .record-sources a:hover,
  .source-ref-list a:hover {{
    background: var(--cobalt-soft);
  }}

  .source-register a:hover {{
    background: #edf4f1;
  }}
}}

@media (width <= 1100px) {{
  .site-header {{
    grid-template-columns: auto 1fr auto;
  }}

  .record-masthead-illustrated {{
    grid-template-columns: minmax(0, 1fr) minmax(220px, 305px);
    gap: 30px 40px;
  }}

  .record-masthead-illustrated .record-heading {{
    grid-area: 1 / 1;
  }}

  .record-masthead-illustrated .school-record-portrait {{
    grid-area: 1 / 2 / span 2;
  }}

  .record-masthead-illustrated .record-coverage {{
    grid-area: 2 / 1;
    width: 100%;
  }}
}}

@media (width <= 820px) {{
  html {{
    scroll-padding-top: 116px;
  }}

  .site-header {{
    min-height: 108px;
    height: auto;
    grid-template-columns: 1fr auto;
    gap: 2px 12px;
    padding: 8px 18px 0;
  }}

  .site-header nav {{
    grid-area: 2 / 1 / auto / -1;
    width: 100%;
    height: 46px;
  }}

  .site-header nav a {{
    min-height: 44px;
    min-width: 0;
    padding-inline: 6px;
    font-size: 12px;
  }}

  .site-header nav a::after {{
    left: 8px;
    right: 8px;
    bottom: 3px;
  }}

  .snapshot-mark {{
    padding-inline: 10px;
  }}

  .briefing-view,
  .compare-view,
  .school-view,
  .evidence-view {{
    min-height: calc(100svh - 108px);
    padding-left: 20px;
    padding-right: 20px;
  }}

  .briefing-view {{
    padding-top: 0;
    padding-bottom: 92px;
  }}

  .compare-view,
  .school-view,
  .evidence-view {{
    padding-top: 54px;
    padding-bottom: 90px;
  }}

  .briefing-hero {{
    grid-template-columns: 1fr;
    gap: 42px;
    min-height: 0;
    padding: 54px 0 48px;
  }}

  .briefing-hero h1 {{
    font-size: clamp(52px, 11vw, 72px);
  }}

  .briefing-inventory {{
    max-width: 640px;
  }}

  .release-board {{
    padding-top: 52px;
  }}

  .release-board-heading {{
    gap: 22px;
  }}

  .briefing-principles {{
    margin-top: 70px;
    padding-top: 42px;
  }}

  .comparison-toolbar {{
    padding: 16px;
  }}

  .comparison-canvas {{
    border-radius: 12px;
    padding: 17px 11px 11px;
  }}

  .evidence-hero {{
    gap: 30px;
  }}

  .record-masthead {{
    grid-template-columns: 1fr;
    gap: 26px;
    min-height: 0;
    padding: 30px;
  }}

  .record-masthead-illustrated {{
    grid-template-columns: minmax(0, 1fr) minmax(150px, .52fr);
    gap: 18px 24px;
  }}

  .record-masthead-illustrated .record-heading {{
    grid-area: 1 / 1;
  }}

  .record-masthead-illustrated .school-record-portrait {{
    grid-area: 1 / 2;
    height: 270px;
    margin: -22px -10px -28px 0;
  }}

  .record-masthead-illustrated .record-coverage {{
    grid-area: 2 / 1 / auto / -1;
  }}

  .record-school-rail {{
    display: none;
  }}

  .record-domain-tabs {{
    display: flex;
    margin-top: 16px;
    overflow-x: auto;
  }}

  .record-domain-tabs button {{
    flex: 1 0 165px;
    min-width: 165px;
  }}

  .record-workspace {{
    grid-template-columns: 1fr;
    gap: 30px;
  }}

  .series-index {{
    display: flex;
    position: static;
    overflow-x: auto;
    border-radius: 10px;
  }}

  .series-index > p {{
    flex: 0 0 125px;
    min-width: 125px;
    border-right: 1px solid var(--line);
    border-bottom: 0;
  }}

  .series-index > a {{
    flex: 0 0 210px;
    min-width: 210px;
    border-right: 1px solid var(--line);
    border-bottom: 0;
  }}

  .series-index > a.active {{
    border-left: 0;
    border-bottom: 3px solid var(--cobalt);
  }}

  .ledger-header {{
    grid-template-columns: 1fr;
    gap: 17px;
  }}

  .ledger-provenance {{
    justify-items: start;
    text-align: left;
  }}

  .ledger-table-scroll {{
    margin-right: 0;
  }}

  .evidence-record {{
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 18px;
  }}

  .source-register > div {{
    grid-template-columns: repeat(2, 1fr);
  }}
}}

@media (width <= 520px) {{
  .site-header {{
    padding-inline: 15px;
  }}

  .wordmark strong {{
    font-size: 13px;
  }}

  .wordmark > span {{
    width: 32px;
    height: 32px;
  }}

  .briefing-hero {{
    padding-top: 46px;
  }}

  .briefing-hero h1 {{
    font-size: clamp(44px, 13.2vw, 56px);
    line-height: .94;
  }}

  .briefing-deck {{
    margin-top: 22px;
    font-size: 16px;
    line-height: 1.62;
  }}

  .briefing-actions {{
    display: grid;
  }}

  .briefing-actions a {{
    width: 100%;
  }}

  .briefing-inventory div {{
    min-height: 106px;
    padding: 15px;
  }}

  .briefing-inventory dd {{
    font-size: 27px;
  }}

  .release-board-heading h2,
  .briefing-principles h2 {{
    font-size: 41px;
  }}

  .release-table-shell {{
    border-radius: 10px;
  }}

  .principle-grid {{
    grid-template-columns: 1fr;
    border-radius: 10px;
  }}

  .principle-grid article {{
    min-height: 220px;
  }}

  .view-intro h1,
  .evidence-hero h1 {{
    font-size: 44px;
  }}

  .record-masthead {{
    padding: 24px 21px;
    border-radius: 11px;
  }}

  .record-masthead h1 {{
    font-size: 43px;
  }}

  .record-masthead-illustrated {{
    grid-template-columns: minmax(0, 1fr) 118px;
    gap: 14px;
  }}

  .record-masthead-illustrated .school-record-portrait {{
    height: 210px;
    margin: -14px -20px -22px 0;
  }}

  .record-coverage {{
    min-width: 0;
    padding: 14px 15px;
  }}

  .record-domain-tabs button {{
    flex-basis: 145px;
    min-width: 145px;
  }}

  .ruler-contract {{
    padding: 17px;
  }}

  .ledger-table-tools {{
    grid-template-columns: 1fr auto auto;
  }}

  .ledger-table-tools label {{
    grid-column: 1 / -1;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }}

  .result-mobile-cards {{
    gap: 12px;
  }}

  .evidence-record {{
    padding: 16px;
  }}

  .source-register > div {{
    grid-template-columns: 1fr;
  }}

  .record-evidence-header,
  .trace-header {{
    padding: 34px 22px 22px !important;
  }}

  .record-evidence-body,
  .trace-body {{
    padding: 24px 22px 40px;
  }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
  }}
}}
"""


def apply_premium_presentation(css: str) -> str:
    """Append the presentation system to a compatible compiled stylesheet."""

    if PREMIUM_PRESENTATION_MARKER in css:
        return css

    required_selectors = (
        ".site-header{",
        ".briefing-hero{",
        ".record-masthead{",
        ".ledger-table{",
    )
    missing = [selector for selector in required_selectors if selector not in css]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Unable to apply premium presentation: missing bundle selectors {joined}"
        )

    return f"{css}\n{PREMIUM_PRESENTATION_CSS.strip()}\n"
