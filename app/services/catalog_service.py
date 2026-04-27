import asyncio
from app.core.tmdb_client import AsyncTMDBClient

async def fetch_catalog(tmdb_client: AsyncTMDBClient, provider_id: int, category: str, content_type: str, limit: int = 40) -> list:
    methods = {
        'popular': tmdb_client.get_popular,
        'top_rated': tmdb_client.get_top_rated,
        'recent': tmdb_client.get_recent,
        'trending': tmdb_client.get_trending
    }
    fetch_method = methods.get(category)
    
    if not fetch_method:
        return []

    combined = []
    
    # Calculate pages needed (20 items per page from TMDB)
    # Ex: limit 40 -> 2 pages, limit 60 -> 3 pages
    pages_to_fetch = max(1, limit // 20)
    
    if content_type in ['movie', 'tv']:
        results = await fetch_method(content_type, provider_id, pages=pages_to_fetch)
        for r in results: 
            r['stremio_type'] = 'movie' if content_type == 'movie' else 'series'
        combined = results
        
    elif content_type == 'combined':
        movies_task = fetch_method('movie', provider_id, pages=pages_to_fetch)
        tv_task = fetch_method('tv', provider_id, pages=pages_to_fetch)
        
        movies, series = await asyncio.gather(movies_task, tv_task)
        
        for m in movies: m['stremio_type'] = 'movie'
        for s in series: s['stremio_type'] = 'series'
        
        combined = movies + series
        
    # Tri forcé et absolu en Python pour TOUS les modes (film, tv, combined)
    # pour pallier aux imprécisions de l'ordre de TMDB lors de la fusion des pages
    if category == 'top_rated':
        combined.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
    elif category == 'recent':
        def get_date(x):
            date_str = x.get('primary_release_date') or x.get('first_air_date')
            return date_str if date_str else '1970-01-01'
        combined.sort(key=get_date, reverse=True)
    elif category == 'trending':
        combined.sort(key=lambda x: x.get('vote_count', 0), reverse=True)
    else: # popular
        combined.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        
    # On renvoie exactement le nombre demandé (après le tri pour avoir le vrai top)
    return combined[:limit]