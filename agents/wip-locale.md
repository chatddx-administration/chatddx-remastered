# Locale: work in progress

The portal in more than one language: its pages, its islands and the words its own code says, in the language of the
person reading them. "Decided" means the user said so; "Take" is the agent's recommendation and still open.

The name is `locale`, as `:Translations` is the domain's already: a chunk that carries a recipe's texts into a case's
language, with its own Library tab and page (`src/chatddx/portal/translations.py`). A locale is the portal's language,
never what is sent to a model.

It is a package of its own, `chatddx.locale` (`src/chatddx/locale/`): the catalogs, what reads them at boot, the
callables that say a message in the request's locale, and what keeps the catalogs in step with the code. The portal is
the only package that says what it says through it, and it keeps only how it does: its templates' callables, the
middleware on its app and the messages of its own.

## Start with this

1. **Decided: gettext, with Babel**, one catalog for the server and the islands. English is the source: a message's
   English is its key, and a request no catalog fits is answered in English, as every page is now.
2. **Take: Swedish first**, beside English. Both have one plural form besides the singular, so nothing in the first
   step needs more than gettext's plurals.
3. **Take: the portal only.** The API, the repl, the CLI and the docs stay English.
4. **Take: the browser's language first**, `Accept-Language`, matched against the catalogs there are; a switch of the
   person's own comes after (see "Open").
5. **Decided: what clinicians and researchers read is localized; what developers and ops read is raw.** A whoops says
   what is going on and what the person can do now, its `message`, which is translated where it is shown, and what
   they are to pass on to developers and ops, its `pass_on`, which isn't (`src/chatddx/whoops.py:Whoops`).
6. **Decided: numbers and dates are written one way, whatever the locale.** A number by a simple global default, a space
   between thousands and a decimal point (`1 000.34`); a date as ISO writes it (`2026-10-23 14:16`).

## What there is to translate

| Where                               | How much                        | Held as                                 |
| ----------------------------------- | ------------------------------- | --------------------------------------- |
| the templates                       | ~510 runs of text, ~2,600 words | text between tags, Jinja expressions    |
| the islands                         | ~150 runs of text, ~970 words   | Svelte markup, and messages built in TS |
| attributes of both                  | ~90                             | `placeholder`, `aria-label` and `title` |
| the portal's Python                 | ~95 strings, ~650 words         | `SHELVES` above all                     |
| what the portal shows from below it | open-ended                      | findings and API errors, by code        |
| what data sets hold                 | open-ended                      | schemas' names, titles and descriptions |

The templates are in `src/chatddx/portal/templates/` and the islands in `frontend/src/`; `SHELVES` is
`src/chatddx/portal/shelves.py:SHELVES`.

Some 600 to 800 messages, of which three habits of the templates make more work than their count:

- **Sentences put together from pieces**, such as `{{ k.mine }} yours · {{ k.seen - k.mine }} shared with you`, a
  fragment added under an `{% if %}`, and `"Pick none" if every else "Pick every one shown"`. A translator needs the
  whole sentence, to put its words in another order.
- **A kind's word dropped into a sentence**, as `word | replace("_", " ")` is in many places. Swedish inflects it
  (konfiguration, konfigurationen) and compounds it, so a word dropped in reads wrong more often than not.
- **English plurals by hand**, `"" if n == 1 else "s"`, in 13 places.

The rest holds already: dates are written `%Y-%m-%d %H:%M` (`src/chatddx/portal/pages.py:_when`), which Swedish
reads as it is, and `src/chatddx/portal/templates/base.html` has a `lang` to set.

## How it works

### The catalog

Built: one `.po` file a locale in `src/chatddx/locale/catalogs/`, `sv.po` begun empty, packaged with `chatddx.locale`
and read at boot (`src/chatddx/locale/locale.py:Locales`) with Babel's `read_po`, then turned into a gettext catalog in
memory: no compiled file in git or in the build. A message whose translation is missing or fuzzy is said in English.

Built: boot fails on a catalog that doesn't parse, or whose reviewed translations' `%(name)s` placeholders aren't their
messages', which Babel's catalog checks find. A fuzzy translation is left out of that, as it isn't said; what is left
to translate is a flag, not a failure (see "Checks"). A message with no translation is written anew from the code each
time, so that Babel matches a changed message only to one translated.

### The server

- **The locale**, built: picked a request at a time, from `Accept-Language` against the catalogs there are, with
  Babel's `negotiate_locale` (`src/chatddx/locale/locale.py:Locales.negotiate`). `src/chatddx/portal/pages.py:page`
  sets it around the page's rendering (`src/chatddx/locale/locale.py:saying`) and gives it as `locale`, whose `tag` is
  `base.html`'s `lang`.
- **The templates**, built: Jinja's `i18n` extension, newstyle and trimmed, on `src/chatddx/portal/pages.py:templates`,
  with `_()`, `ngettext()`, `pgettext()`, `npgettext()` and `{% trans %}…{% pluralize %}`. The callables read the
  locale set around the rendering rather than the template's context, which a macro imported without context, as most
  are, doesn't see. Newstyle escapes what is put into a message and fails on a placeholder left out, so a message with
  a `%` of its own writes it `%%`, and `ngettext()`'s count is `%(num)s` unless it is given a name.
- **The portal's Python**, built, marks what it says with a no-op `N_()` where it is defined, as `SHELVES` is at
  import, and the template that shows it translates it with `_()`. What a function says in answer to a request is
  translated where it is said, from the request's locale, which `src/chatddx/locale/locale.py:Saying`, a middleware on
  the portal's app, sets around each request; `page` still sets it around rendering, as a page answering an
  unexpected error is rendered outside the middleware. A message is written as a template's are, and besides:
  - translated and filled in one call, `tr("…%(name)s…", name=…)` (`src/chatddx/locale/locale.py:tr`), never an
    f-string, and `%(given)r` where the English quotes what was typed;
  - with the callables imported by name, never as `_`, which the code uses to discard a value, and so `tr` where a
    template says `_`;
  - a word drawn from a fixed set, such as a configuration's purpose or a part of a response, from a table of
    `pgettext_noop` marks, translated with `pgettext()` and the same context.
- **A kind's word**, built: drawn by one filter, `{{ word | kind }}`, translated with `pgettext("kind", …)` from
  `src/chatddx/portal/shelves.py:_WORDS`, which a no-op `pgettext_noop` marks and boot holds to the kinds shelved, so
  that whether Swedish translates it is decided in the catalog (see "Open"). A list of kinds is sorted by its words as
  said (`src/chatddx/portal/shelves.py:Shelved.worded`).
- **How a message is written**, as every page's are:
  - a sentence whole, its alternatives each a message (`_("None you see of these.") if … else _("None you see.")`);
  - a sentence with links or markup in it a `{% trans %}` block, the markup in its message;
  - what is set apart by `·` a message apiece, the separator left out;
  - anything counted with `ngettext()`, even where English says it the same either way (`%(num)s yours`), as Swedish
    doesn't;
  - a word that could be read more ways than one, or a note that follows a button, with `pgettext()` and a context
    naming what it is or follows (`"outcome"`, `"after the button Run the picked"`);
  - a sentence a kind's word agrees with, such as `A new configuration`, a message per kind, as `begun.html`'s
    titles are, since Swedish says `en ny` or `ett nytt` by the word;
  - two counts in one sentence each counted on its own, then put into a sentence of its own
    (`_("%(queued)s, %(under_way)s.", queued=ngettext(…), under_way=ngettext(…))`);
  - no variable of a template named `_`, which is the callable that translates.

  A message's translation is trusted markup, as newstyle marks it safe: an apostrophe in it is written as itself, not
  as `&#39;`, which tests reading a page's HTML meet.

### The islands

- **The catalog** an island needs, built, is put in its page, as its props are: `base.html`'s
  `<script type="application/json" id="locale">`, holding the locale's tag and the reviewed translation of each message
  said in `frontend/src/`, and of each whoops, which the API may answer an island with
  (`src/chatddx/locale/locale.py:Locale.islands`, made at boot); nothing on a page without an island.
- **`t()`**, built (`frontend/src/lib/locale.ts`), looks a message up and puts its `%(name)s` placeholders in, the same
  placeholders as the server's, so one check covers both; `tn()`, `tp()` and `tnp()` are gettext's `ngettext`,
  `pgettext` and `npgettext`; a plural picks its form with `Intl.PluralRules`, whose `one` and `other` are gettext's two
  forms for English and Swedish. A message given nothing for a placeholder throws, as the server's do.
- **How an island writes a message**, built, as a template does, and besides:
  - a sentence with markup in it is `{@html th(…)}`, a translation being trusted markup as the server's are, and what
    is put into it escaped, as a `{% trans %}` block's variables are;
  - what the server says too is said with the server's message, context and placeholders, so that it is translated
    once: an outcome's word (`frontend/src/lib/runs/outcomes.ts`), a kind's (`frontend/src/lib/kinds.ts`), `view
    %(n)s`, `%(sent)s in, %(got)s out`;
  - a list of words is put together by the page's locale (`listed()`, `Intl.ListFormat`);
  - a table of words defined at a module's top is translated there, as an island's script runs once the page that
    holds its catalog is parsed.
- **A whoops**, built, is `Whoops(message, pass_on)`: the API answers it with `detail`, its message, and `pass_on`, as
  it is; the error page says the one in the request's locale and the other after `Pass this on to ops, as it is:`, and
  so does an island (`frontend/src/lib/api/client.ts:why`).
- **Dates and numbers** an island writes are written as the server writes them, whatever the locale (see "Start with
  this"): a date `%Y-%m-%d %H:%M`, and a number, as yet, without the space between thousands (see "Steps").

### Extraction

Built: `chatddx locale write` extracts, with Babel, what the portal's Python says, its tests left out; what a whoops
says, wherever in `src/chatddx/` it is raised, in the context `whoops`; the templates, with Jinja's `babel_extract`;
and the islands' `t()`, `tn()`, `tp()`, `tnp()` and `th()` in `.svelte` and `.ts`, with
`src/chatddx/locale/locale.py:_islands`, their tests, declarations and shadcn's components left out. It brings each
catalog up to that, a changed message fuzzy with its closest translation, and begins a catalog of each tag it is given,
such as `chatddx locale write sv`. A catalog keeps which file says each message but not the line, so that moving code
leaves it as it is, and the file is how the islands' share is told. It fails on a message said both counted and not in
the same context, which gettext holds as one plural message, leaving the other untranslatable.

### Checks

- **`chatddx locale check`**, built: the `locale` stage of `scripts/check.sh`, when `src/chatddx/` or the frontend
  changed, fails while a catalog is behind the code and flags what is left untranslated or fuzzy, a human's to settle as
  stamps pending are. At the baseline, a catalog behind is flagged, and what is left to translate isn't.
- **Tests**: the ones there were stay English, as no request of theirs asks for another language. Built: in
  `src/chatddx/locale/test/test_locale.py`, a request's language negotiated, boot failing on wrong placeholders, the
  islands' messages found, a catalog kept in step with the code, and the islands' share of a catalog; in
  `src/chatddx/portal/test/test_localized.py`, a reviewed message said in a macro imported without context and a fuzzy
  one not, a page's `lang`, the catalog only in an island's page, and the shelves, a 404's detail and a form's refusal
  said in the request's locale, the shelves sorted by their headings as said. `frontend/src/lib/locale.test.ts`: `t()`
  and its kin, in English and in a catalog's locale. In a browser (`src/chatddx/portal/test/test_browser.py`), an island
  said in Swedish, a plural put into a sentence among it; and a whoops said in Swedish with what it passes on as it is
  (`src/chatddx/portal/test/test_lab.py`).

## Steps

Each step leaves the portal working in English, and Swedish appearing only where messages are reviewed.

1. **The plumbing**, built: Babel as a dependency, which uv2nix takes into the flake from `uv.lock`; the locale in
   `page`, the `i18n` extension, `lang`, an empty `sv.po`, the boot check, the extractor and the check in
   `scripts/check.sh`. Nothing marked, nothing seen to change.
2. **`base.html`, the macros and the Library**, built: each sentence made whole, each plural made `ngettext`, each
   kind's word drawn by `kind`, each message marked; 122 messages. What the Library still says in English comes from
   the portal's Python, the shelves' headings and what each kind is, and waits for step 4.
3. **The other pages**, built: Review, the Lab, Scoring, Runs, a run's, a thread's and a case's, the World, and every
   template besides; 613 messages in all. Every page rendered in a locale that brackets each message it says leaves
   unbracketed only the name ChatDDX, data (names, tags, a schema's field names) and what comes from the portal's
   Python and the API, which step 4 and step 6 take.
4. **The portal's Python**, built: `SHELVES`, the refusals of `src/chatddx/portal/fields.py` and of each module's
   routes, the 404s of an address that names nothing, and what the modules name things by (`, an earlier version`,
   `view %(n)s`); 709 messages in all, 96 of them the Python's. What the portal shows from below it stays English:
   the API's and the bench's refusals, pydantic's messages, a scorer's problems and a JSON error's, which step 6
   takes.
5. **The islands**, built: `t()` and its kin, the catalog in the page, each message marked, and a whoops's two parts;
   964 messages in all, 324 of them the islands', 73 of which the server says too. Every island page opened in a
   locale that brackets each message leaves unbracketed only data, symbols, and what the API says, which step 6
   takes.
6. **Findings and API errors**: a message a code, with its parameters, where one is written, else the English as it
   comes (`src/chatddx/portal/pages.py:refusable`).
7. **Swedish**: Take: an agent drafts each translation marked fuzzy, which gettext leaves unsaid, and a human reviews
   it by clearing the mark.
8. **Numbers**: the global default, `1 000.34`, wherever the server and the islands write a number, counts put into
   messages among them.

## Open

1. **The person's own language**: a switch in the header that sets a cookie, or a language of the person's kept in the
   store, which `src/chatddx/identity/identity.py:Person` has no field for, with `Accept-Language` the default either
   way.
2. **The kinds' words**: translated, kept as the glossary's (they are the API's, the docs' and the address's,
   `?kind=configuration`), or both, as the Library is to teach the data model. Step 2 draws them in one place, so this
   is settled in the catalog whenever it is.
3. **Refusals**: they are English. A code for each, translated where shown; translated where shown with the English as
   the key, as a whoops's `said` is; or English for now. A whoops is settled (see "Start with this").
4. **What data sets hold**: a schema's titles and descriptions in more than one language is a question of the data
   format, and left out of these steps.
5. **A locale with more plural forms** than one and other: the islands' `t()` would need gettext's forms in the order
   of CLDR's categories, which Babel derives its own from.
