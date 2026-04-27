import httpx
from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio

class AsyncTMDBClient:
    def __init__(self, api_key: str, region: str = 'FR', language: str = 'fr-FR'):
        self.base_url = "https://api.themoviedb.org/3"
        self.default_params = {
            'api_key': api_key,
            'watch_region': region,
            'language': language
        }
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _fetch_discover(self, media_type: str, provider_id: int, extra_params: Dict[str, Any], pages: int = 2) -> list:
        params = self.default_params.copy()
        params['with_watch_providers'] = provider_id
        params.update(extra_params)
        
        url = f"{self.base_url}/discover/{media_type}"
        
        async def fetch_page(page: int):
            p = params.copy()
            p['page'] = page
            try:
                response = await self.client.get(url, params=p)
                response.raise_for_status()
                return response.json().get('results', [])
            except Exception as e:
                print(f"Error fetching from TMDB: {e}")
                return []

        tasks = [fetch_page(i) for i in range(1, pages + 1)]
        pages_results = await asyncio.gather(*tasks)
        
        results = []
        for page_res in pages_results:
            results.extend(page_res)
            
        # Optimisation & Filtrage : Exclure spécifiquement les "Animés" (Animation japonaise)
        # Genre 16 = Animation. original_language = 'ja' = Japonais.
        filtered_results = [
            r for r in results 
            if not (r.get('original_language') == 'ja' and 16 in r.get('genre_ids', []))
        ]
        
        return filtered_results

    async def get_popular(self, media_type: str, provider_id: int, pages: int = 2) -> list:
        return await self._fetch_discover(media_type, provider_id, {'sort_by': 'popularity.desc'}, pages)

    async def get_top_rated(self, media_type: str, provider_id: int, pages: int = 2) -> list:
        return await self._fetch_discover(media_type, provider_id, {'sort_by': 'vote_average.desc', 'vote_count.gte': 300}, pages)

    async def get_recent(self, media_type: str, provider_id: int, pages: int = 2) -> list:
        sort_param = 'primary_release_date.desc' if media_type == 'movie' else 'first_air_date.desc'
        date_lte_param = 'primary_release_date.lte' if media_type == 'movie' else 'first_air_date.lte'
        today = datetime.now().strftime('%Y-%m-%d')
        
        return await self._fetch_discover(media_type, provider_id, {
            'sort_by': sort_param,
            date_lte_param: today,
            'vote_count.gte': 2 # Évite les films/séries complètement inconnus avec 0 vote
        }, pages)

    async def get_trending(self, media_type: str, provider_id: int, pages: int = 2) -> list:
        # "Les plus cherchés": On cherche la popularité par le nombre de votes
        # sur les sorties des 2 dernières années (730 jours) pour s'assurer
        # d'avoir assez de résultats même sur les petits catalogues comme Paramount+
        date_field = 'primary_release_date.gte' if media_type == 'movie' else 'first_air_date.gte'
        last_months = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        params = {
            'sort_by': 'vote_count.desc',
            date_field: last_months
        }
        return await self._fetch_discover(media_type, provider_id, params, pages)

    async def close(self):
        await self.client.aclose()