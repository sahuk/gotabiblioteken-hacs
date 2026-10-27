---
name: translation-review
description: Review the integration's human-language translations (entity names, setup dialog, generated text such as "Closed" or "Not staffed") with one cheap native-speaker reviewer agent per language, then summarize and discuss before changing anything. Use before a release when user-facing text changed, or when asked to review translations. "Translation" here means natural languages (Swedish, German, ...), not code.
---

# Translation review

Reviews the text users read, in every language listed in TRANSLATIONS.md
except English (the source). Each language gets its own reviewer agent,
briefed **in that language** and running on a cheap model. You collect the
results, summarize them, and discuss with the user. Nothing is applied until
the user decides.

## 1. Build the packets

```bash
uv run scripts/translation_review_packets.py <scratchpad>/translation-review [--since <ref>] [--all] [--lang xx ...]
```

- The default compares with the latest `v*` tag and reviews only strings that changed since then, in that language or in its English source. `--all` reviews everything. `--since` takes any git ref. `--lang` limits the run to some languages.
- If it prints `nothing to review`, tell the user and stop.
- Otherwise, read `index.json`. It lists each language with its packet path and changed keys. Read one packet, so you know what the reviewers will see: the changed strings next to the English, real output on three sample days, the concepts, and the full translation file and labels.

## 2. Write each brief in the reviewer's language

For every language in `index.json`, write the brief yourself, fresh, **in that language**. Don't store or reuse briefs between runs. Use natural, native wording, not a word-for-word translation of the template. Cover these points:

1. You are a native speaker of <language> reviewing the <language> text of a Home Assistant integration that shows Götabiblioteken's opening hours.
2. Name what is new or changed. Use the changed keys, and say what each one is in plain words (an entity name, a state, part of the Markdown card).
3. Read the packet at `<packet path>`. Focus on the changed strings and on whether they fit the existing terms in the same file.
4. Check:
   - correctness and grammar;
   - natural wording;
   - the terms libraries in that language area actually use;
   - length: names follow a short place name and get cut off from the right;
   - Home Assistant's capitalization style in that language;
   - that nothing can be misread (for example, "not staffed" read as "closed").
5. Do not modify any files.
6. Answer in English, in at most 250 words:
   1. Verdict: `ok` / `minor fixes` / `needs changes`.
   2. A table: key | current | suggestion | severity (`error` / `improvement` / `nit`) | rationale.
   3. Uncertainties.

## 3. Launch every reviewer at once

Send all the Agent calls in **one message**, so the reviewers run in parallel. For each call, set:
- `subagent_type: "general-purpose"`
- `model: "haiku"`
- `description: "<Language> translation review"`

Wait for every result. Don't summarize from a partial set; if the user asks how it's going, say which reviewers are still running.

## 4. Summarize, then discuss

Give the user one summary:

- **Verdict counts:** which languages said `ok`, `minor fixes` or `needs changes`. Say whether any reviewer found an error.
- **Suggested changes:** a table of language | current | suggested | why | **my take**. Your take is either "take" or "keep", with a reason. Weigh the suggestion against consistency with existing terms, against the length and cut-off risk, and against the spec in `docs/ux/personas.md`.
- **One decision for the user:** the same idea raised by several reviewers, such as a different wording for the same concept in many languages. Present it as a choice with your recommendation.
- **Accepted trade-offs:** issues that reviewers flagged but that have no good fix.

Say that the reviewers are a cheap AI model. Their claims about which terms libraries really use are weaker evidence than a native speaker's. When one reviewer's suggestion contradicts a term an earlier review settled (see the git log of the translation files), prefer the settled term unless the reasoning is clearly better.

Then **stop and ask** which changes to make. Never apply anything before the user decides.

## 5. Apply what the user approves

- **Entity names and the setup dialog:** edit `custom_components/gotabiblioteken/translations/<lang>.json`. If English changes, change `strings.json` to match (it is a copy of `en.json`).
- **Generated text:** edit `LABELS_<LANG>` in `custom_components/gotabiblioteken/data.py`.
- **Tests:** update the expected strings in `tests/test_localization.py`, `tests/test_data.py` and `tests/test_entities.py` where they cover the changed text.
- **TRANSLATIONS.md:** update the note on how many AI review rounds the translations have had.
- **CHANGELOG.md:** add the changes under `## [Unreleased]`.
- Run the full pre-commit chain from CLAUDE.md before committing.

## Rules

- Don't review English.
- Library names (Borensberg, Motala, ...) are place names and are never translated.
- Language codes are matched exactly, as in Home Assistant (see TRANSLATIONS.md). Don't propose regional variants as part of a review.
