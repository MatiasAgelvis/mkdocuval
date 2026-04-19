# TODO

## 1. Review current document pipeline
- Confirm source canonical format: `ODT/` remains primary.
- Document current active build flow:
  - `ODT/` → `DOCX/` via Pandoc (`docusaurus_nb.py`)
  - `DOCX/` → `docs/fichas/<name>.md` via Mammoth + HTML post-processing
- Identify brittle spots:
  - Mammoth HTML output conversion
  - regex-based title/page extraction
  - intermediate `DOCX/` stage and unused `PDF/` directory
  - implicit pattern inference instead of explicit file mapping

## 2. Evaluate MarkItDown and Textract as replacements
- Test `markitdown` conversion for `DOCX` → Markdown.
- Check if `markitdown` can consume `ODT` directly or via `DOCX`.
- Compare output quality against current `mammoth` + regex cleanup.
- Test `textract` for structured extraction from `ODT`/`DOCX` and other formats.
- Evaluate a schema-first export path:
  - JSON
  - XML
  - SQLite
- Decide whether to keep Pandoc for `ODT` → `DOCX` only for legacy support, or use `textract` as the primary intake tool and structured output generator.
- Status: current pipeline already emits `cards.json` via `generate_cards_json.py`; further `markitdown`/`textract` evaluation can be postponed until frontend needs improved extraction.

## 3. Rebuild parser pipeline
- Replace current `docusaurus_nb.py` conversion step with a cleaner, minimal toolchain.
- Create a new converter script with explicit stages:
  - `ODT/` input (or direct `textract` intake from multiple source formats)
  - optional `DOCX/` intermediate storage only if needed for compatibility, preferably in a temp directory or in-memory stream
  - preferred direct JSON/SQLite output rather than Markdown as the primary artifact
  - use `mammoth.extract_raw_text` for DOCX text extraction to ignore formatting and extract plain content
  - extract any embedded images and save them alongside generated content
  - record image references in the JSON metadata, including source file and position context
- Keep the parsing approach simple:
  - use one primary extraction library if possible
  - avoid multiple conversion tools unless needed
  - use file metadata / filename mapping for structure instead of complex heuristics
  - images are only references, not OCR or content extraction
- Add structured metadata extraction for each card:
  - title
  - slug
  - source filename
  - page numbers or citation info
  - summary / excerpt
  - optional image references
- Status: implemented in `generate_cards_json.py` with ODT/DOCX intake, direct JSON output, embedded image extraction, and structured metadata.

## 4. Generate frontend-friendly data
- Emit consumable artifacts for a custom frontend / Svelte + Vite app:
  - `cards.json`
  - optional `cards.sqlite` or `cards.db`
- Build a search index during conversion:
  - full-text searchable content
  - title, tags, metadata fields
  - optional separate `search_index.json`
- Keep the data static and use client-side search in the browser.
- Status: `cards.json` generation is working; search index and optional SQLite export remain to be added.

## 5. Custom frontend and CMS plan
- Build a static Svelte + Vite frontend for browsing and document assembly.
- Use static JSON/SQLite output for fast browsing and search.
- Keep the website completely static as the primary goal.
- Treat PocketBase as an optional convenience utility only if needed for quick edits, not as a source of truth.
- Prefer a static site build with generated content over a hybrid backend.
- Status: still pending; focus first on frontend proof-of-concept with `cards.json`.

## 6. Documentation updates
- Update `README.md` with the new conversion pipeline.
- Add notes about the pipeline decision and chosen tooling.
- Track the status of the rebuild in this TODO file.
- Status: README still documents the old MkDocs flow and should be updated.

## 7. AI-assisted features
- Explore using an LLM or semantic vectorizer to generate tags, summaries, or cross-card references from the extracted content in `cards.json`.
- Prototype a simple script to analyze the generated JSON and suggest tags or related cards based on content similarity.
- Consider adding an optional "AI insights" section to each card in the frontend based on this analysis.
- Status: still an open idea; can be prototyped after the initial JSON generation is stable.

## 7. Immediate action items
- [x] Review and document the current document pipeline in code comments.
- ~[ ] Prototype `markitdown` conversion for existing `DOCX` files.~ -> Cancelled
- [x] Define JSON/SQLite schema for index cards, including image references.
- [x] Decide on PocketBase use case vs static-only approach. -> Static-only
- [ ] Create Svelte + Vite prototype folder and data loading plan.
- [ ] Update `README.md` and pipeline docs to reflect current JSON workflow.
- [ ] Build initial browser-side search/index plan for `cards.json`.
- [ ] Prototype automated tag generation / cross-card reference discovery from `cards.json` using an LLM or semantic vectorizer.
