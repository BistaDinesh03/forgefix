# Monetization (planned, not enabled)

!!! note "Status"
    This is a **plan**, not a product. There is no billing code, no account system,
    and no paywall in the repository. The CLI stays free and MIT-licensed.

## Model

| Tier | Price | What it is |
| --- | --- | --- |
| **CLI (forever free, MIT)** | $0 | Everything in this repository: doctor, up, report, serve, plugins |
| **Hosted dashboard** | Paid subscription | Health tracking for **private** repositories, historical scores, org-wide rollups |
| **Team seats** | Per seat/month | Shared dashboards, SSO, audit log for organizations |
| **Sponsored rule packs** | Partner-funded, free to users | Industry-specific check packs (e.g. healthcare, fintech onboarding baselines) sponsored by companies that want those standards adopted |

## Why this shape

- The value that must stay open is exactly the value that builds trust: the checks
  themselves and the deterministic scoring. Keeping them MIT maximizes adoption and
  makes the free tier genuinely complete for public repos.
- The sustainable wedge is **history and aggregation**: a public repo can be scanned by
  anyone at any time; *private* repos over *time*, across a *team*, is work people pay
  for.
- Sponsored rule packs keep the core independent: partners fund development of
  specialized checks that everyone gets for free, and the sponsorship is disclosed.

## Ground rules

1. No feature of the CLI is crippled to sell the hosted product.
2. The hosted service adds storage, history, and collaboration — never exclusive checks.
3. The license does not change. Ever.
4. Telemetry in the CLI: none today, none without an explicit opt-in announcement.

## Stub command

`forgefix cloud` prints:

```text
Hosted version coming soon - see docs/monetization.md
```

That is deliberately all it does.
