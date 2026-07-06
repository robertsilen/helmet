import argparse
import math
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

OMDBAPI_KEY = os.environ["OMDBAPI_KEY"]

FINNA_SEARCH_URL = "https://api.finna.fi/v1/search"
OMDB_URL = "https://www.omdbapi.com/"
PAGE_SIZE = 100

# Fields returned by Finna by default, plus "genres" which isn't included
# unless explicitly requested. Once you list any field[], Finna stops
# returning its defaults, so we have to spell all of them out here.
RECORD_FIELDS = [
    "id",
    "title",
    "year",
    "buildings",
    "formats",
    "genres",
    "images",
    "languages",
    "nonPresenterAuthors",
    "onlineUrls",
    "presenters",
    "rating",
    "series",
    "subjects",
]

# Friendly aliases for Finna's format facet values. Any value not listed here
# is passed straight through to the API (case as given), so less common
# formats still work as long as you know Finna's exact facet token.
FORMAT_ALIASES = {
    "dvd": "DVD",
    "bluray": "BluRay",
    "blu-ray": "BluRay",
}

# Helmet branch name -> Finna building facet code. Finna's public API doesn't
# expose a lookup endpoint for this (the facet listing only ever returns the
# top-level "0/Helmet/" node), so this table was built by sampling the
# `buildings` field across real DVD/BluRay search results. Helmet's branch
# network changes rarely, but if a branch is missing or renamed, pass its
# building code directly (e.g. "2/Helmet/e/e17/") instead of a name.
LIBRARY_CODES = {
    "aineistohotelli helsinki": "2/Helmet/h/h03/",
    "aineistohotelli helsinki lapset": "2/Helmet/h/h03l/",
    "aineistohotelli vantaa": "2/Helmet/v/v33/",
    "aineistohotelli vantaa lapset": "2/Helmet/v/v33l/",
    "arabianranta": "2/Helmet/h/h56/",
    "arabianranta lapset": "2/Helmet/h/h56l/",
    "entresse": "2/Helmet/e/e76/",
    "entresse lapset": "2/Helmet/e/e76l/",
    "etelä-haaga": "2/Helmet/h/h32/",
    "etelä-haaga lapset": "2/Helmet/h/h32l/",
    "hakunila": "2/Helmet/v/v20/",
    "hakunila lapset": "2/Helmet/v/v20l/",
    "hankinta espoo": "2/Helmet/e/e03/",
    "hankinta helsinki": "2/Helmet/h/hhh/",
    "hankinta helsinki lapset": "2/Helmet/h/hhhl/",
    "haukilahti": "2/Helmet/e/e17/",
    "haukilahti lapset": "2/Helmet/e/e17l/",
    "herttoniemi": "2/Helmet/h/h80/",
    "herttoniemi lapset": "2/Helmet/h/h80l/",
    "iso omena": "2/Helmet/e/e23/",
    "iso omena lapset": "2/Helmet/e/e23l/",
    "itäkeskus": "2/Helmet/h/h90/",
    "itäkeskus lapset": "2/Helmet/h/h90l/",
    "jakomäki": "2/Helmet/h/h77/",
    "jakomäki lapset": "2/Helmet/h/h77l/",
    "jätkäsaari lapset": "2/Helmet/h/h18l/",
    "kalajärvi": "2/Helmet/e/e97/",
    "kalajärvi lapset": "2/Helmet/e/e97l/",
    "kalasatama lapset": "2/Helmet/h/h58l/",
    "kallio": "2/Helmet/h/h53/",
    "kallio lapset": "2/Helmet/h/h53l/",
    "kannelmäki": "2/Helmet/h/h42/",
    "kannelmäki lapset": "2/Helmet/h/h42l/",
    "karhusuo": "2/Helmet/e/e81/",
    "karhusuo lapset": "2/Helmet/e/e81l/",
    "kauklahti": "2/Helmet/e/e78/",
    "kauklahti lapset": "2/Helmet/e/e78l/",
    "kauniainen": "2/Helmet/k/k01/",
    "kauniainen lapset": "2/Helmet/k/k01l/",
    "kirjastoauto espoo": "2/Helmet/e/e02/",
    "kirjastoauto helsinki": "2/Helmet/h/h02/",
    "kirjastoauto helsinki lapset": "2/Helmet/h/h02l/",
    "kirjastoauto vantaa": "2/Helmet/v/v32/",
    "kirjastoauto vantaa lapset": "2/Helmet/v/v32l/",
    "koivukylä": "2/Helmet/v/v40/",
    "koivukylä lapset": "2/Helmet/v/v40l/",
    "kontula": "2/Helmet/h/h94/",
    "kontula lapset": "2/Helmet/h/h94l/",
    "kotipalvelu espoo": "2/Helmet/e/ekp/",
    "käpylä": "2/Helmet/h/h61/",
    "käpylä lapset": "2/Helmet/h/h61l/",
    "laajalahti": "2/Helmet/e/e14/",
    "laajalahti lapset": "2/Helmet/e/e14l/",
    "laajasalo": "2/Helmet/h/h84/",
    "laajasalo lapset": "2/Helmet/h/h84l/",
    "laaksolahti": "2/Helmet/e/e73/",
    "laaksolahti lapset": "2/Helmet/e/e73l/",
    "lauttasaari": "2/Helmet/h/h20/",
    "lauttasaari lapset": "2/Helmet/h/h20l/",
    "lippulaiva": "2/Helmet/e/e32/",
    "lippulaiva lapset": "2/Helmet/e/e32l/",
    "lumo": "2/Helmet/v/v45/",
    "lumo lapset": "2/Helmet/v/v45l/",
    "länsimäki": "2/Helmet/v/v28/",
    "länsimäki lapset": "2/Helmet/v/v28l/",
    "malmi": "2/Helmet/h/h70/",
    "malmi lapset": "2/Helmet/h/h70l/",
    "malminkartano": "2/Helmet/h/h41/",
    "malminkartano lapset": "2/Helmet/h/h41l/",
    "martinlaakso": "2/Helmet/v/v62/",
    "martinlaakso lapset": "2/Helmet/v/v62l/",
    "maunula": "2/Helmet/h/h63/",
    "maunula lapset": "2/Helmet/h/h63l/",
    "mosaiikki": "2/Helmet/v/v70/",
    "mosaiikki lapset": "2/Helmet/v/v70l/",
    "munkkiniemi": "2/Helmet/h/h33/",
    "munkkiniemi lapset": "2/Helmet/h/h33l/",
    "myllypuro": "2/Helmet/h/h92/",
    "myyrmäki": "2/Helmet/v/v60/",
    "myyrmäki lapset": "2/Helmet/v/v60l/",
    "nöykkiö": "2/Helmet/e/e30/",
    "nöykkiö lapset": "2/Helmet/e/e30l/",
    "oodi": "2/Helmet/h/h00/",
    "oodi lapset": "2/Helmet/h/h00l/",
    "otaniemi": "2/Helmet/e/e15/",
    "otaniemi lapset": "2/Helmet/e/e15l/",
    "oulunkylä": "2/Helmet/h/h64/",
    "oulunkylä lapset": "2/Helmet/h/h64l/",
    "paloheinä": "2/Helmet/h/h67/",
    "paloheinä lapset": "2/Helmet/h/h67l/",
    "pasila": "2/Helmet/h/h01/",
    "pasila kirjavarasto": "2/Helmet/h/hva/",
    "pasila lapset": "2/Helmet/h/h01l/",
    "pikku huopalahti lapset": "2/Helmet/h/h30l/",
    "pohjois-haaga": "2/Helmet/h/h40/",
    "pohjois-haaga lapset": "2/Helmet/h/h40l/",
    "point": "2/Helmet/v/v51/",
    "point lapset": "2/Helmet/v/v51l/",
    "puistola": "2/Helmet/h/h76/",
    "puistola lapset": "2/Helmet/h/h76l/",
    "pukinmäki": "2/Helmet/h/h72/",
    "pukinmäki lapset": "2/Helmet/h/h72l/",
    "pähkinärinne": "2/Helmet/v/v68/",
    "pähkinärinne lapset": "2/Helmet/v/v68l/",
    "rikhardinkatu": "2/Helmet/h/h13/",
    "rikhardinkatu lapset": "2/Helmet/h/h13l/",
    "ristikko": "2/Helmet/h/h37/",
    "ristikko lapset": "2/Helmet/h/h37l/",
    "roihuvuori": "2/Helmet/h/h82/",
    "roihuvuori lapset": "2/Helmet/h/h82l/",
    "sakarinmäki lapset": "2/Helmet/h/h89l/",
    "saunalahti": "2/Helmet/e/e33/",
    "saunalahti lapset": "2/Helmet/e/e33l/",
    "sello": "2/Helmet/e/e01/",
    "sello lapset": "2/Helmet/e/e01l/",
    "suomenlinna": "2/Helmet/h/h19/",
    "suomenlinna lapset": "2/Helmet/h/h19l/",
    "suurpelto": "2/Helmet/e/e25/",
    "suurpelto lapset": "2/Helmet/e/e25l/",
    "suutarila": "2/Helmet/h/h74/",
    "suutarila lapset": "2/Helmet/h/h74l/",
    "tapanila": "2/Helmet/h/h73/",
    "tapanila lapset": "2/Helmet/h/h73l/",
    "tapiola": "2/Helmet/e/e10/",
    "tapiola lapset": "2/Helmet/e/e10l/",
    "tapulikaupunki": "2/Helmet/h/h75/",
    "tapulikaupunki lapset": "2/Helmet/h/h75l/",
    "tikkurila": "2/Helmet/v/v30/",
    "tikkurila lapset": "2/Helmet/v/v30l/",
    "tikkurila musiikkivarasto": "2/Helmet/v/v34/",
    "töölö": "2/Helmet/h/h25/",
    "töölö lapset": "2/Helmet/h/h25l/",
    "vallila": "2/Helmet/h/h55/",
    "vallila lapset": "2/Helmet/h/h55l/",
    "viherlaakso": "2/Helmet/e/e71/",
    "viherlaakso lapset": "2/Helmet/e/e71l/",
    "viikki": "2/Helmet/h/h71/",
    "viikki lapset": "2/Helmet/h/h71l/",
    "vuosaari": "2/Helmet/h/h98/",
    "vuosaari lapset": "2/Helmet/h/h98l/",
}


def resolve_format(fmt):
    return FORMAT_ALIASES.get(fmt.lower(), fmt)


def resolve_library(name):
    """Resolve a branch name to its Finna building code. Falls back to
    treating the input as a literal building code (e.g. "2/Helmet/e/e17/")
    if it's not a known branch name."""
    key = name.strip().lower()
    if key in LIBRARY_CODES:
        return LIBRARY_CODES[key]
    if name.count("/") >= 2:
        return name
    raise ValueError(
        f'Unknown library "{name}". Pass one of the known Helmet branch names '
        f'(e.g. "Iso Omena", "Oodi", "Haukilahti") or a raw building code.'
    )


def request_with_retry(session_or_requests, url, params, max_retries=5, retry_delay=5):
    """GET with exponential backoff, honoring Retry-After on 429s."""
    for attempt in range(max_retries):
        response = session_or_requests.get(url, params=params)
        if response.status_code == 200:
            return response
        wait = int(response.headers.get("Retry-After", retry_delay))
        print(f"Attempt {attempt + 1} failed with status code {response.status_code}")
        if attempt < max_retries - 1:
            print(f"Retrying in {wait} seconds...")
            time.sleep(wait)
            retry_delay *= 2
    return response


def fetch_catalog(formats, libraries=None, genres=None):
    """Fetch Helmet video catalog records for the given formats.

    formats: list of Finna format tokens (e.g. ["DVD", "BluRay"]).
    libraries: optional list of branch names/codes; results are restricted,
        server-side, to titles held at one of these branches (OR'd together).
    genres: optional list of Finna genre facet values (e.g. "Lastenelokuvat");
        results are restricted, server-side, to titles tagged with one of
        these genres (OR'd together).
    """
    building_filters = [("filter[]", f'~building:"{resolve_library(lib)}"') for lib in libraries or []]
    if not building_filters:
        building_filters = [("filter[]", '~building:"0/Helmet/"')]

    genre_filters = [("filter[]", f'~genre_facet:"{genre}"') for genre in genres or []]

    field_params = [("field[]", field) for field in RECORD_FIELDS]

    seen_ids = set()
    results = []

    for fmt in formats:
        finna_format = resolve_format(fmt)
        page = 1
        total_pages = 1
        while page <= total_pages:
            params = [
                ("filter[]", f'~format:"1/Video/{finna_format}/"'),
                *building_filters,
                *genre_filters,
                *field_params,
                ("limit", PAGE_SIZE),
                ("page", page),
            ]
            response = request_with_retry(requests, FINNA_SEARCH_URL, params)
            response.raise_for_status()
            data = response.json()
            count = data.get("resultCount", 0)
            total_pages = math.ceil(count / PAGE_SIZE) if count else 0

            for record in data.get("records", []):
                if record["id"] in seen_ids:
                    continue
                seen_ids.add(record["id"])
                record["format"] = finna_format
                record["url"] = "https://helmet.finna.fi/Record/" + record["id"]
                results.append(record)

            print(f"[{finna_format}] page {page}/{total_pages}, {len(results)} collected so far")
            page += 1

    return results


def lookup_omdb(session, title, year=None):
    """Look up a title on OMDb, preferring an exact year match, falling back
    to a title-only lookup if the year doesn't match anything."""
    params = {"t": title, "apikey": OMDBAPI_KEY}
    if year:
        params["y"] = year

    response = request_with_retry(session, OMDB_URL, params, max_retries=3)
    result = response.json() if response is not None else {}
    status_code = response.status_code if response is not None else None

    if year and result.get("Response") == "False":
        del params["y"]
        response = request_with_retry(session, OMDB_URL, params, max_retries=3)
        result = response.json() if response is not None else {}
        status_code = response.status_code if response is not None else None

    return result, status_code


def add_omdb_data(records, output_path):
    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
                "Connection": "keep-alive",
            }
        )

        for i, item in enumerate(records, start=1):
            title = item.get("title")
            year = item.get("year")
            if not title:
                continue

            omdbapi, status_code = lookup_omdb(session, title, year)
            item["omdbapi_statuscode"] = status_code

            if omdbapi.get("Response") == "False":
                print(f"Processed {i} of {len(records)} items. No data: {title}")
                item["omdbapi_found"] = "no data"
            else:
                print(f"Processed {i} of {len(records)} items. Found: {title} (IMDb {omdbapi.get('imdbRating', 'N/A')})")
                item["omdbapi_found"] = "ok"
                item["omdbapi_title"] = omdbapi["Title"]
                item["omdbapi_year"] = omdbapi["Year"]
                item["omdbapi_Rated"] = omdbapi["Rated"]
                item["omdbapi_Runtime"] = omdbapi["Runtime"]
                item["omdbapi_Genre"] = omdbapi["Genre"]
                item["omdbapi_Director"] = omdbapi["Director"]
                item["omdbapi_Writer"] = omdbapi["Writer"]
                item["omdbapi_Actors"] = omdbapi["Actors"]
                item["omdbapi_imdbRating"] = omdbapi["imdbRating"]
                item["omdbapi_imdbVotes"] = omdbapi["imdbVotes"]
                item["omdbapi_imdbID"] = omdbapi["imdbID"]
                item["omdbapi_Type"] = omdbapi["Type"]
                item["omdbapi_Metascore"] = omdbapi["Metascore"]

                for r in omdbapi.get("Ratings", []):
                    if r["Source"] == "Internet Movie Database":
                        item["omdbapi_IMDB_rating"] = r["Value"]
                    if r["Source"] == "Rotten Tomatoes":
                        item["omdbapi_Rotten_Tomatoes_rating"] = r["Value"]
                    if r["Source"] == "Metacritic":
                        item["omdbapi_Metacritic_rating"] = r["Value"]

            if i % 1000 == 0:
                save_xlsx(sort_by_imdb_rating(records), output_path)
                print(f"Checkpoint: saved {i} items to {output_path}")

    save_xlsx(sort_by_imdb_rating(records), output_path)


def parse_imdb_rating(r):
    try:
        return float(r.get("omdbapi_imdbRating"))
    except (TypeError, ValueError):
        return None


def sort_by_imdb_rating(records):
    """Sort by IMDb rating (best first); ties broken by year, then title
    (both ascending). Missing values sort after present ones within their
    tie group."""

    def sort_key(r):
        rating = parse_imdb_rating(r)
        neg_rating = -rating if rating is not None else float("inf")
        try:
            year = int(r.get("omdbapi_year"))
        except (TypeError, ValueError):
            year = float("inf")
        title = (r.get("title") or "").lower()
        return (neg_rating, year, title)

    return sorted(records, key=sort_key)


def save_xlsx(records, output_path):
    df = pd.DataFrame(records)
    df.to_excel(output_path, index=False)


def print_summary(args, records):
    with_rating = sum(1 for r in records if parse_imdb_rating(r) is not None)
    without_rating = len(records) - with_rating
    print("\nSearch summary:")
    print(f"  format:  {args.format}")
    print(f"  library: {args.library}")
    print(f"  genre:   {args.genre}")
    print(f"  found:   {len(records)} titles")
    print(f"  with IMDb rating:    {with_rating}")
    print(f"  without IMDb rating: {without_rating}")


def print_top_rated(records, top_n=20):
    rated = [(parse_imdb_rating(r), r.get("title")) for r in records]
    rated = [(rating, title) for rating, title in rated if rating is not None]
    rated.sort(key=lambda x: x[0], reverse=True)

    print(f"\nTop {min(top_n, len(rated))} by IMDb rating:")
    for rank, (rating, title) in enumerate(rated[:top_n], start=1):
        print(f"#{rank}. {title} (IMDb {rating})")


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Helmet library video catalog data.")
    parser.add_argument(
        "--format",
        nargs="+",
        default=["DVD", "BluRay"],
        help="Video formats to fetch, e.g. --format dvd bluray (default: dvd bluray).",
    )
    parser.add_argument(
        "--library",
        nargs="+",
        help='One or more Helmet branch names to restrict results to, '
        'e.g. --library "Iso Omena" Oodi. Omit to include all Helmet branches.',
    )
    parser.add_argument(
        "--genre",
        nargs="+",
        help='One or more Finna genre tags to restrict results to, '
        'e.g. --genre Lastenelokuvat (children\'s films). Matches Finna\'s '
        "genre facet exactly (case-sensitive). Omit to include all genres.",
    )
    parser.add_argument(
        "--output",
        default="output.xlsx",
        help="Output xlsx filename (default: output.xlsx).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt and proceed straight to OMDb enrichment.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        records = fetch_catalog(args.format, args.library, args.genre)
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    print(
        f"\nFound {len(records)} titles matching "
        f"format={args.format} library={args.library} genre={args.genre}.\n"
    )

    if not records:
        return

    save_xlsx(records, args.output)

    proceed = args.yes
    if not proceed:
        answer = input("Add IMDb/OMDb details (rating, cast, genre, etc.) to these titles? [y/N]: ")
        proceed = answer.strip().lower() in ("y", "yes")

    if proceed:
        add_omdb_data(records, args.output)
        print_summary(args, records)
        print_top_rated(records)

    print(f"\nSaved {len(records)} titles to {args.output}")


if __name__ == "__main__":
    main()
