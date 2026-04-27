from typing import List

def format_to_stremio_meta(tmdb_item: dict) -> dict:
    item_type = tmdb_item.get('stremio_type', 'movie')
    title = tmdb_item.get('title') or tmdb_item.get('name', 'Inconnu')
    tmdb_id = str(tmdb_item.get('id'))
    stremio_id = f"tmdb:{tmdb_id}"

    poster_path = tmdb_item.get('poster_path')
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

    release_year = ""
    date_str = tmdb_item.get('primary_release_date') or tmdb_item.get('first_air_date')
    if date_str and len(date_str) >= 4:
        release_year = date_str[:4]

    return {
        "id": stremio_id,
        "type": item_type,
        "name": title,
        "poster": poster_url,
        "description": tmdb_item.get('overview', ''),
        "releaseInfo": release_year
    }

def format_catalog_response(metas: List[dict]) -> dict:
    return {"metas": metas}