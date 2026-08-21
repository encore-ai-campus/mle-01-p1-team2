# Shared Animal Rescue UI Theme Design

## Goal

Make `main.py` and every Python page under `pages/` feel like one product by
sharing the visual language of the approved `home.py` landing page while
preserving all existing data, search, map, chart, and RAG behavior.

## Scope

In scope:

- Shared colors, typography, spacing, surfaces, borders, shadows, tabs,
  inputs, alerts, tables, charts, and sidebar styling.
- A branded Streamlit sidebar and consistent navigation labels in `main.py`.
- A reusable page-header pattern for secondary pages.
- Consistent panel framing for data, hospital, and RAG content.
- A compatibility layer so a page can still be run directly during local
  development.
- Tests for generated theme markup, UTF-8 safety, and Python compilation.

Out of scope:

- Changing CSV, SQLite, Chroma, RAG, map, or chart data processing.
- Adding new dependencies.
- Replacing the existing home hero composition.
- Implementing new navigation actions inside static HTML cards.

## Design Direction

The visual system uses the home page tokens:

- Ink: deep navy for headings and primary controls.
- Purple: the primary accent for active navigation and focus states.
- Lavender: soft background fills for chips, filters, and selected tabs.
- Warm yellow: the secondary highlight for key statistics.
- White surfaces: rounded cards with thin lavender-gray borders and subtle
  shadows.
- Noto Sans KR as the preferred font with a system fallback.

The home page remains the visual landing-page variant. Secondary pages use
the same tokens, sidebar, page header, cards, and controls but keep layouts
appropriate to their content.

## Architecture

### `src/ui_theme.py`

This new module owns shared presentation concerns:

- `apply_theme()` injects one idempotent CSS block into Streamlit.
- `render_page_header(eyebrow, title, description)` renders the common
  eyebrow, title, and explanatory copy.
- `render_panel_header(title, meta=None)` renders a reusable card heading.
- `render_sidebar_brand()` renders the branded sidebar content that appears
  before Streamlit's navigation.

The helper functions only render UI. They do not import data modules, read
files, mutate application data, or call navigation actions.

### `main.py`

`main.py` sets page configuration, applies the theme, renders the brand area,
and defines the navigation tree with readable Korean page labels. It remains
the only place that owns the application-level `st.navigation` call.

### Page modules

Each page calls `apply_theme()` and `render_page_header()` before its existing
content. Existing data loading and business logic stay in the same page
module. Streamlit-native charts, dataframes, chat controls, alerts, and maps
are styled by shared selectors rather than rewritten into HTML.

`home.py` keeps its custom hero and dashboard CSS, but the shared theme is
loaded first so it inherits the global font, background, and control tokens.

## Page Treatments

| Page | Header | Main treatment |
| --- | --- | --- |
| Home | Landing hero | Existing hero, overview cards, service cards |
| Data | Data insights | Styled tabs containing the three chart views |
| Data2 | Pet data dashboard | Styled chart panels and consistent chart spacing |
| Hospital | Hospital finder | Filter panel, result panel, map panel |
| RAG | Disease inquiry | Filter panel, chat surface, evidence cards |

## Error and Empty States

Existing `st.warning`, `st.success`, `st.error`, and `st.info` calls remain in
place. The shared theme gives them consistent rounded borders, muted fills,
accent colors, and readable text. No new fallback behavior is introduced.

## Compatibility and Encoding

- All new source content must be UTF-8 safe.
- Emoji used in Python string literals must use single-codepoint `\\UXXXXXXXX`
  escapes or ASCII-safe symbols; UTF-16 surrogate pairs are forbidden.
- `main.py` and page modules must compile independently.
- The theme must not depend on Streamlit APIs that are unavailable in the
  repository's declared Streamlit version.

## Verification

- Unit tests assert the theme exposes required CSS selectors and page-header
  markup.
- A rendered-HTML test asserts generated markup contains no surrogate code
  points and can be encoded as UTF-8.
- Compile every `main.py` and `pages/*.py` file.
- Run the focused UI tests and the existing test suite; report unrelated
  failures caused by missing legacy modules or unavailable dependencies.
