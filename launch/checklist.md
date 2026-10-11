# Launch checklist (day by day)

Rules of the road: no fake claims, no star begging, no bots, no cross-post spam. One
genuine post per community, and engage with every reply honestly.

## Day -2 (polish)

- [ ] `make test lint type` green; CI matrix green on a fresh push
- [ ] Demo GIF regenerated (`make gif`) and under 3 MB
- [ ] README renders correctly on github.com (GIF, tables, badges)
- [ ] SECURITY.md contact reachable; private vulnerability reporting enabled in repo settings
- [ ] Topics set: `devtools`, `cli`, `python`, `dx`, `setup`, `docker`, `security`, `oss`
- [ ] v0.1.0 tag pushed; GitHub release published; PyPI trusted publisher configured
- [ ] Read launch drafts in `launch/` and personalize them (they're templates, not final copy)

## Day -1 (soft seed)

- [ ] Send the repo to 5–10 people who hit the onboarding problem (no public post yet)
- [ ] Fix every bug they find; merge with attribution in CHANGELOG
- [ ] Pre-write the Show HN post timed for ~9–11am ET on a weekday

## Day 1 (launch)

- [ ] Show HN (text post, honest limitations section included)
- [ ] r/opensource post
- [ ] r/Python post (angle: Typer/FastAPI + deterministic scoring)
- [ ] r/devops post (angle: CI gate + HTTP API)
- [ ] X thread (hook -> demo -> CTA), link the GIF
- [ ] Reply to every comment for the first 48 hours; no defensive answers

## Day 2–3

- [ ] Product Hunt launch (tagline + first comment drafted in `launch/producthunt.md`)
- [ ] First awesome-list PR (pick the single best-fit list from `launch/awesome-prs.md`)
- [ ] Triage issues; label `good first issue` for anything a newcomer can pick up

## Day 4–7

- [ ] Second awesome-list PR (different list, spaced out)
- [ ] Publish a short postmortem: what launched, what broke, what's next
- [ ] Update ROADMAP from real feedback; cut a v0.1.1 if warranted
- [ ] Thank contributors publicly in the release notes

## Ongoing

- [ ] Weekly Dependabot triage
- [ ] Monthly: regenerate demo GIF if the CLI output changed
- [ ] Never buy coverage, never ask for stars, never automate engagement
