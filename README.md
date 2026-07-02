# spain-dnv-consultant

**A Claude Code template for self-filing the Spanish digital-nomad residence
permit (*teletrabajo de carácter internacional*, Ley 14/2013) — initial and
renewal.**

*Шаблон Claude Code для самостоятельной подачи на ВНЖ цифрового кочевника в
Испании (teletrabajo internacional) — первичная подача и продление.*

> ⚠️ **This is not legal advice.** It produces **drafts that require independent
> verification** against official sources and, where the stakes warrant, a
> qualified lawyer. The engine never files, pays, or registers anything on your
> behalf. **Read [LEGAL_DISCLAIMER.md](LEGAL_DISCLAIMER.md) before using this.**
> — *Это не юридическая консультация. См. [LEGAL_DISCLAIMER.md](LEGAL_DISCLAIMER.md).*

---

## What this is

Fork it, open it in [Claude Code](https://claude.com/claude-code), and a set of
bundled skills walks you through assembling a renewal (or initial) application:
an intake interview, curated legal research, cross-checking your claims, filling
the forms, two review passes, and a ready-to-file package. The content is
**Russian-primary with Spanish legal terminology**, matching how the target
applicant actually works.

The skills and agents live in `.claude/` and **activate automatically** when you
open the folder in Claude Code — there is nothing to install.

## What it is *not*

- **Not a lawyer, not legal advice, no warranty.** See
  [LEGAL_DISCLAIMER.md](LEGAL_DISCLAIMER.md).
- **Not a filing bot.** It never submits an application, pays a *tasa*, or
  registers an *expediente*. Every binding, irreversible step is yours.
- **Not a substitute for official sources.** Thresholds (IPREM/SMI), forms, and
  fees change by year; the engine flags what must be re-checked live.
- **Not general.** It targets **one archetype** (see Scope). Other profiles need
  adaptation.

## Who it's for

A **technically comfortable self-filer** who wants an organized, well-researched
draft they will then validate themselves — not someone looking to outsource the
decision. Community chat experience surfaced here is **opinion, not law**, and is
labeled as such.

## Scope (one archetype)

Autónomo / independent contractor for a foreign company, renewing the DNV permit,
with a spouse (*cónyuge*) as a dependent family member. The framework is
**Ley 14/2013** (as amended by Ley 28/2022), competent authority **UGE-CE**,
electronic filing.

## How it works — the pipeline

Each step is a skill you invoke in Claude Code. Later steps check that their
prerequisites ran (see `user/pipeline-state.schema.md`):

```
/dnv-intake        → your case profile (single source of truth, stored locally)
   ├─ /dnv-research    → curated + live legal research  → notes
   │     └─ /dnv-synthesis  → a working spec from your profile + research
   │            └─ /dnv-verify   → adversarial claim-by-claim check (devils-advocate)
   ├─ /dnv-chat-mining → (optional) mine your own Telegram exports, locally
   └─ /dnv-documents   → fill the forms deterministically
          └─ /dnv-review    → field-QA + re-derivation + "Spanish official" pass
                 └─ /dnv-submission → ready-to-file checklist + monitoring + escalation
```

The `engine/` directory holds the deterministic Python behind the skills
(form-filling, field QA, claim extraction, the local chat anonymizer).

## Requirements

- **Claude Code** (desktop, CLI, or IDE extension).
- **Python 3** for the engine scripts — **standard library only**, nothing to
  `pip install`.
- **Optional:** a Perplexity MCP server for live research; without it, research
  degrades gracefully to built-in web search and flags the degradation.

## Quick start

1. Fork this repo and clone your fork.
2. Open the folder in Claude Code.
3. Run `/dnv-intake` and answer the interview. Your answers are written **only**
   to your local `user/` workspace (gitignored) — never committed.
4. Follow the pipeline above. Read every draft critically; the engine tells you
   what still needs live verification or a professional's eyes.

## Bring your own data — privacy model

- Your personal data (profile, documents, chat exports) lives in `user/`, which
  is **gitignored**. It stays on your machine.
- The only community data shipped in this template is an **anonymized, aggregated
  digest** (no per-author identifiers). You can mine your *own* fresh chat
  exports locally with `/dnv-chat-mining`; the raw text never leaves `user/`.
- This repository was assembled by copying only de-personalized assets and was
  independently audited for PII before publication.

## Status

Early. Renewals under this regime are among the **first wave** (original permits
date from 2023), so administrative precedent is thin and this template will keep
evolving. Treat it as a well-organized starting point, not a finished authority.

## Contributing

Contributions are welcome, but note: an automated fail-closed PII gate
(pre-commit + CI) is **planned but not yet wired in**. Until it lands, do not
commit any real personal data — see [docs/PII_GATE_NOTES.md](docs/PII_GATE_NOTES.md).

## License

[MIT](LICENSE). The knowledge-base prose describes public legal norms; verify
against primary sources (BOE, UGE-CE) before relying on it.
