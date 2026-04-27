from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.user_config import decode_config, encode_config
from app.core.config import settings
from app.core.tmdb_client import AsyncTMDBClient
from app.services.catalog_service import fetch_catalog
from app.models.stremio import format_to_stremio_meta, format_catalog_response
from app.utils.cache import catalog_cache
import os
from pathlib import Path

router = APIRouter()

# Get the absolute path to the templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)

# Configure Page
@router.get("/configure", response_class=HTMLResponse)
async def configure(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="configure.html",
        context={"providers": settings.PROVIDERS}
    )

# Main manifest
@router.get("/manifest.json")
async def get_base_manifest():
    return await get_manifest("{}")

# Configured manifest
@router.get("/{config}/manifest.json")
async def get_manifest(config: str):
    user_config = decode_config(config) if config != "{}" else {}
    
    catalogs = []
    
    for provider_name, catalogs_config in user_config.items():
        if provider_name not in settings.PROVIDERS:
            continue
        
        # Handle old config format for backward compatibility
        if not isinstance(catalogs_config, dict):
            catalogs_config = {
                "top_rated": catalogs_config,
                "popular": catalogs_config,
                "trending": catalogs_config,
                "recent": catalogs_config
            }
            
        cat_titles = {
            "top_rated": "Les mieux Notés",
            "popular": "Les plus Populaires",
            "trending": "Les plus Cherchés",
            "recent": "Les plus Récents"
        }
        
        for cat_name, content_type in catalogs_config.items():
            if content_type == "none" or not content_type:
                continue
                
            cat_title = cat_titles.get(cat_name, cat_name.title())
            base_id = f"tor_{provider_name.lower().replace('+', 'plus').replace(' ', '_')}_{cat_name}"
            
            if content_type == "both":
                catalogs.append({
                    "type": "movie",
                    "id": base_id,
                    "name": f"{provider_name} - {cat_title}"
                })
                catalogs.append({
                    "type": "series",
                    "id": base_id,
                    "name": f"{provider_name} - {cat_title}"
                })
            else:
                stype = "movie" if content_type in ["movie", "combined"] else "series"
                catalogs.append({
                    "type": stype,
                    "id": base_id,
                    "name": f"{provider_name} - {cat_title}"
                })

    manifest = {
        "id": "com.tor.catalog",
        "version": "1.0.0",
        "name": "Tor Catalog",
        "description": "Optimized streaming platform catalogs for Stremio.",
        "types": ["movie", "series"],
        "catalogs": catalogs,
        "resources": ["catalog"],
        "behaviorHints": {
            "configurable": True,
            "configurationRequired": True if config == "{}" else False
        }
    }
    
    return JSONResponse(content=manifest)

# Catalog Route
@router.get("/{config}/catalog/{type}/{id}.json")
@router.get("/{config}/catalog/{type}/{id}/{extra}.json")
async def get_catalog(config: str, type: str, id: str, extra: str = None):
    # Cache key
    cache_key = f"{config}_{type}_{id}"
    if cache_key in catalog_cache:
        return JSONResponse(content=catalog_cache[cache_key])

    user_config = decode_config(config)
    
    # We must find the provider key robustly.
    # The ID format is tor_{provider_slug}_{category}
    # Example: tor_prime_video_top_rated
    # We know the ID starts with tor_
    
    id_without_tor = id[4:] # Remove "tor_"
    
    provider_name = None
    provider_id = None
    content_type = None
    category = None
    
    for name, p_id in settings.PROVIDERS.items():
        provider_slug = name.lower().replace('+', 'plus').replace(' ', '_')
        if id_without_tor.startswith(provider_slug + "_"):
            # Found the provider!
            category = id_without_tor[len(provider_slug) + 1:] # Everything after the slug
            if name in user_config:
                provider_name = name
                provider_id = p_id
                
                c_config = user_config[name]
                if isinstance(c_config, dict):
                    content_type = c_config.get(category)
                else:
                    content_type = c_config # old format
            break
                
    if not provider_name or not content_type or content_type == "none":
        print(f"DEBUG: Failed resolving provider. id: {id}, slug: {provider_slug}, config: {user_config}")
        return JSONResponse(content={"metas": []})

    country = user_config.get("country", "FR")
    tmdb_client = AsyncTMDBClient(
        api_key=settings.TMDB_API_KEY,
        region=country,
        language="fr-FR"
    )
    if not settings.TMDB_API_KEY:
        print("CRITICAL: TMDB_API_KEY is empty in settings!")
    
    # Read the custom limit from user config, defaulting to 40
    try:
        limit = int(user_config.get("limit", 40))
    except (ValueError, TypeError):
        limit = 40
        
    try:
        actual_content_type = content_type
        if content_type == "both":
            actual_content_type = 'movie' if type == 'movie' else 'tv'
            
        results = await fetch_catalog(tmdb_client, provider_id, category, actual_content_type, limit=limit)
        metas = [format_to_stremio_meta(r) for r in results]
        response_data = format_catalog_response(metas)
        
        # Save to cache
        catalog_cache[cache_key] = response_data
        
        return JSONResponse(content=response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"INTERNAL SERVER ERROR on fetch_catalog: {e}")
        return JSONResponse(content={"metas": []})
    finally:
        await tmdb_client.close()