# Reference Parity Map: `your_spotify` -> `spotify2` (Streamlit)

## Scope and baseline
This document maps the UX and interaction model from `https://github.com/Yooooomi/your_spotify` to this Python/Streamlit implementation.

Reference surfaces inspected:
- Routes: `apps/client/src/App.tsx`
- Sidebar/nav model: `apps/client/src/components/Layout/Sider/useLinks.tsx`, `Sider.tsx`
- Global interval UI: `apps/client/src/components/Header/Header.tsx`, `components/IntervalSelector/IntervalSelector.tsx`, `services/intervals.ts`
- Core pages: `scenes/Home/Home.tsx`, `AllStats/AllStats.tsx`, `Tops/*`, entity detail scenes (`ArtistStats`, `TrackStats`, `AlbumStats`), `Settings/Settings.tsx`, importer flow.

## Interaction model parity

### Navigation parity
Reference pattern:
- Persistent left navigation grouped by category.
- Category-level IA: General, Tops, Settings (+ optional collaborative section).
- Global search from sidebar with drill-down to Artist/Album/Song detail pages.

Streamlit mapping:
- Persistent sidebar navigation with grouped sections and page buttons.
- Global search input in sidebar (Step 2+ behavior; scaffold in Step 1).
- Entity pages include drill-down panels and route-like state using query params/session state.

## Global date-range filter parity
Reference pattern:
- Header-level interval selector on most pages.
- Presets and custom date range dialog.
- Interval controls all charts/lists in page.
- Certain detail pages hide interval selector and rely on route context.

Streamlit mapping:
- Sidebar global date range control (always visible) to fit Streamlit constraints.
- Presets: Today, Yesterday, This Week, Last Week, This Month, Last Month, This Year, Last Year, Last 3 Years.
- Custom start/end date fields.
- Single canonical date-range object in `st.session_state`, used by every query.
- Entity detail views can opt to lock/hide global controls in-page when context requires.

## Page-by-page parity map

| Reference section | Reference behavior | Streamlit page/tab | Parity behavior |
|---|---|---|---|
| Home (`/`) | Welcome header + KPI cards + charts + recent history | Dashboard | Same visual rhythm: KPI cards -> charts -> detailed history/top lists; global date applies everywhere |
| Longest sessions (`/sessions`) | Session-focused ranked analysis | Insights / dedicated block | Session segmentation insights with ranked longest sessions |
| All stats (`/all`) | Dense chart grid for distribution and trend metrics | Insights + Genre Evolution + Diversity | Comparable chart-first analytics grid driven by selected range |
| Top songs (`/top/songs`) | Ranked table, infinite scroll, percentages, drilldown | Songs | Ranked table (plays/minutes/share), pagination, search, drill-down panel |
| Top artists (`/top/artists`) | Ranked table + genres + drilldown | Artists | Ranked table + genre context + artist drill-down |
| Top albums (`/top/albums`) | Ranked table + drilldown | Albums | Ranked album table + album detail |
| Track detail (`/song/:id`) | Context card, counts, first/last, best periods, recents | Songs detail | Same information architecture in Streamlit cards/charts |
| Artist detail (`/artist/:id`) | Rank, first/last, most listened tracks/albums, day repartition | Artists detail | Same order: rank/context -> period highlights -> related entities/charts |
| Album detail (`/album/:id`) | Context, first/last, most listened tracks | Albums detail | Equivalent detail layout |
| Settings (`/settings/*`) | Account/stat/admin tabs, importer, display options | Settings | Connect/import/export/settings sections with clear cards and status states |
| Sidebar search | Artist/track/album jump | Global search affordance | Search across entities and quick open of detail pages |
| Loader + empty states | Loaders and explicit no-data visuals/messages | All pages | Consistent loading skeletons and explicit empty/error cards |

## UX behaviors to replicate
- Clear top-of-page title/subtitle plus right-aligned date control intent.
- Card-based spacing rhythm.
- Tables/lists show both absolute and relative share where relevant.
- Drill-down from top list rows to entity detail views.
- Consistent loading, empty, and error states on every page.
- Search-to-navigate affordance from primary navigation.
- Stateful filtering: switching pages preserves chosen interval.

## Streamlit-specific adaptations
- Streamlit lacks client-side router parity with React routes, so navigation uses sidebar pages + optional query params for detail selection.
- Infinite scroll is replaced by pagination controls while preserving ranked list behavior.
- Header interval selector becomes a persistent sidebar filter for consistency and rerun stability.

## Step 1 status
- This map defines the target UX contract for implementation.
- Step 1 scaffold implements navigation shell + global date state + DB schema/migration base.
