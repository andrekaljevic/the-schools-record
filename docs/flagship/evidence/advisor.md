# Readiness review (advisor)

An independent advisor session with fresh context reviewed commit `7797bb6` on 3 September 2026, re-ran the cheap
gates and spot-checked the remediation. Its opinion, condensed:

**Ready for the owner's review and a preview deployment: yes, with two conditions.** Verified directly: dataset
SHA `245f2d81…9f6f` before and after `tools/build_public_projection.py --check`; `git diff origin/main...HEAD -- data/`
empty; the tests inherited from the anchor commit identical; zero private patterns in `web/dist`; vitest 30/30;
privacy scan 2,629 files clean; security scan 2,550 files clean; budgets met; the author's logs show 53/53 browser
tests and 192/192 Python tests timestamped after the last source edit; only commits on the branch, no amend, reset
or force-push; remote equal to local. Five spot-checks held (unique Eton 2018 anchors linking to records `/0/` and
`/1/`; pre-rendered desktop and mobile comparison panels; no absolute URL without `SITE_URL`; security headers and
"not recorded" receipts in the handler; status-code links resolving).

**Conditions.** (1) Build the preview with `SITE_URL=<preview host>`; the local `web/dist` carries the served
origin `http://127.0.0.1:4321`. (2) Correct stale figures in `EXECUTION.md` (done in the commit after the review:
Python 192, unit 30, end-to-end 53, chart parity 5,460, Lighthouse mobile 94–99).

**Not ready for production cutover:** Chromium only; no form receiver provisioned; no observed CI run yet.

**Look at first.** The remediation commit (`tsr/projection.py`, `web/src/lib/panel.ts`, `web/functions/lib/handler.ts`);
the privacy boundary (`tsr/projection.py` whitelist and scan, `web/scripts/privacy-scan.mjs`, and the fetchable
`web/dist/data/evidence-search.json`); origin handling in `web/astro.config.mjs`.

**Overstated or unverifiable claims, as found.** The stale counts above; "Four reviewers with fresh context" without
saying they were automated sessions (now stated in `jury.md`); the no-JavaScript form path on a plain static host
returns the host's error rather than a receipt (now stated on the forms and in `EXECUTION.md` §7). Lighthouse, the
browser suite, the Python suite and cross-browser evidence were not re-run by the advisor.

**Risks not previously named.** Local `main` was behind `origin/main`, so a diff against local `main` shows
`data/public_sources.json`, which arrived in the anchor commit already on `origin/main`: diff against `origin/main`.
Record page titles repeated the period (fixed after the review). The largest ledger page sits close to its budget.
Headers and form functions are Cloudflare/Netlify-shaped.
