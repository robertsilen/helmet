# helmet
Script to access library data at helmet.fi and enrich with IMDB rating from omdbapi.com

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your [OMDb API](https://www.omdbapi.com/apikey.aspx) key:
   ```
   cp .env.example .env
   ```
   ```
   OMDBAPI_KEY=your_key_here
   ```

## `helmet.py`

A command-line tool that fetches the Helmet library video catalog from the [Finna API](https://api.finna.fi), optionally enriches it with [OMDb](https://www.omdbapi.com/) ratings/cast/genre data, and writes everything to a single xlsx file.

### Usage

```
python helmet.py [--format FORMAT [FORMAT ...]] [--library LIBRARY [LIBRARY ...]] [--genre GENRE [GENRE ...]] [--output OUTPUT] [--yes]
```

- **`--format`** — one or more video formats to fetch, e.g. `--format dvd bluray`. Accepts the friendly aliases `dvd`/`bluray`/`blu-ray`, or any exact [Finna format facet](https://api.finna.fi) token. Defaults to `dvd bluray`.
- **`--library`** — one or more Helmet branch names to restrict results to, e.g. `--library "Iso Omena" Oodi`. Names are resolved to Finna's internal building codes (see `LIBRARY_CODES` in `helmet.py`) and the filter is applied server-side, so only matching titles are fetched in the first place. A raw building code (e.g. `2/Helmet/e/e17/`) also works if a branch is missing from the table. Omit to include all Helmet branches.
- **`--genre`** — one or more Finna genre tags to restrict results to, e.g. `--genre Lastenelokuvat` (children's films) or `Barnfilmer` (the Swedish equivalent). Applied server-side via Finna's genre facet, using the exact capitalization Finna uses. Omit to include all genres.
- **`--output`** — output xlsx filename. Defaults to `output.xlsx`.
- **`--yes`** — skip the confirmation prompt and go straight to OMDb enrichment.

### What it does

1. Queries `api.finna.fi/v1/search` for each requested format, filtered server-side to the requested Helmet branch(es) and genre(s) (or everything, if `--library`/`--genre` are omitted), paginating through all results and tagging each record with its `format` and a `url` link to the Helmet catalog (`https://helmet.finna.fi/Record/<id>`).
2. Prints how many titles matched, then asks whether to fetch OMDb details for them (skip the prompt with `--yes`).
3. If confirmed, looks up each title on OMDb — matching by title **and year** when Finna has a year, falling back to a title-only lookup if that year doesn't match anything — and adds fields such as `omdbapi_title`, `omdbapi_Rated`, `omdbapi_Runtime`, `omdbapi_Genre`, `omdbapi_Director`, `omdbapi_Writer`, `omdbapi_Actors`, `omdbapi_imdbRating`, `omdbapi_imdbVotes`, `omdbapi_imdbID`, `omdbapi_Type`, `omdbapi_Metascore`, plus per-source ratings (`omdbapi_IMDB_rating`, `omdbapi_Rotten_Tomatoes_rating`, `omdbapi_Metacritic_rating`). Requires **`OMDBAPI_KEY`** to be set (via `.env` or the environment). Checkpoints progress to the output file every 1000 items.
4. Writes all fields (raw Finna data, including Helmet's own `genres` tags, plus any OMDb enrichment) to the output xlsx — no intermediate JSON files.

### Known limitations

- Helmet catalog titles are often in Finnish (e.g. "Schindlerin lista"), while OMDb generally only recognizes original/English titles, so some titles won't get a match regardless of year.
- Live "is this specific copy available right now" data isn't available: Finna's API only exposes static bibliographic data (title, format, which branches hold *a* copy), not real-time loan status. That's fetched by the Helmet website itself via a session-protected endpoint, so it isn't exposed here.
- `LIBRARY_CODES` was built by sampling real search results rather than from an official Finna lookup endpoint (none is publicly exposed), so a newly opened or renamed branch might be missing — pass its raw building code as a workaround.
- OMDb's own `omdbapi_Rated` field (after enrichment) is the **US MPAA/TV scale** (G, PG, PG-13, R, TV-Y, TV-G...) — `R` means "Restricted" (17+), not a kids' rating. For an actual kids'-content filter, use `--genre Lastenelokuvat`/`Barnfilmer`, which is Helmet's own cataloging and doesn't require OMDb at all.

### Examples

```
# Blu-rays and DVDs across all Helmet libraries
python helmet.py

# Only Blu-rays held at Tapiola, Haukilahti, Iso Omena, or Lippulaiva, skip the confirmation prompt
python3 helmet.py --format bluray --library "Tapiola" "Haukilahti" "Iso Omena" "Lippulaiva" --yes --output bluray-omena_tapiola_haukilahti_lippulaiva.xlsx
```

```
$ python3 helmet.py --format bluray --library "Haukilahti" "Haukilahti lapset" --genre "Lastenelokuvat" --yes --output haukilahti-bluray.xlsx
[BluRay] page 1/1, 12 collected so far

Found 12 titles matching format=['bluray'] library=['Haukilahti', 'Haukilahti lapset'] genre=['Lastenelokuvat'].

Processed 1 of 12 items. Found: Mary Poppins returns (IMDb 6.7)
Processed 2 of 12 items. No data: Luolamies
Processed 3 of 12 items. Found: Vaiana (IMDb N/A)
Processed 4 of 12 items. No data: Lehmäjengi
Processed 5 of 12 items. No data: Mary ja noidankukka
Processed 6 of 12 items. No data: Räyhä-Ralf valloittaa Internetin
Processed 7 of 12 items. Found: Tarzan (IMDb 4.8)
Processed 8 of 12 items. No data: Miekka kivessä
Processed 9 of 12 items. Found: Viidakkokirja (IMDb N/A)
Processed 10 of 12 items. Found: Pinocchio (IMDb 7.5)
Processed 11 of 12 items. No data: Yli aidan
Processed 12 of 12 items. No data: Riemukas Robinsonin perhe

Search summary:
  format:  ['bluray']
  library: ['Haukilahti', 'Haukilahti lapset']
  genre:   ['Lastenelokuvat']
  found:   12 titles
  with IMDb rating:    3
  without IMDb rating: 9

Top 3 by IMDb rating:
#1. Pinocchio (IMDb 7.5)
#2. Mary Poppins returns (IMDb 6.7)
#3. Tarzan (IMDb 4.8)

Saved 12 titles to haukilahti-bluray.xlsx
```
