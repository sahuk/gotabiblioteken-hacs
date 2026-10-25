# Translations

The integration follows Home Assistant's language: entity names and the
setup dialog come from `custom_components/gotabiblioteken/translations/`, and
the text it generates (closed, weekdays, months, date format, the self-service
label) from `Labels` in `custom_components/gotabiblioteken/data.py`. Any
language not listed here falls back to English.

| Language | Code | Why | Status |
| --- | --- | --- | --- |
| Swedish | `sv` | the libraries' language | native |
| English | `en` | fallback for every other language | native |
| Finnish | `fi` | national minority language of Sweden; Finland | **needs native review** |
| Norwegian Bokmål | `nb` | Norway | **needs native review** |
| Norwegian Nynorsk | `nn` | Norway | **needs native review** |
| Danish | `da` | Denmark | **needs native review** |
| Icelandic | `is` | Iceland | **needs native review** |

The non-Swedish translations are drafts. If you speak one of them, please
check the setup dialog, the entity names (Open, Staffed, Opening hours) and
the generated text, and open an issue or a pull request with corrections.
Library names (Motala, Östra Ryd, …) are place names and are not translated.

## Waiting on Home Assistant

Sweden's other national minority languages are **Meänkieli** (`fit`), the
**Sami** languages (e.g. `se`, `smj`, `sma`), **Romani** and **Yiddish**
(`yi`). Home Assistant can't be set to any of them yet (it only accepts the
languages in `homeassistant.generated.languages`), so a translation file
would never load. They'll be added once Home Assistant supports them;
`tests/test_localization.py` checks that every shipped language is one Home
Assistant accepts.

## Adding a language

1. Copy `translations/en.json` to `translations/<code>.json` and translate
   the values (keep the keys).
2. Add a `LABELS_<CODE>` entry to `LABELS` in `data.py`: closed texts, the
   staffed and self-service labels, the date format and weekday/month names.
3. Add the code to `test_expected_languages` and a row to
   `test_generated_text` in `tests/test_localization.py`, and a row above.
