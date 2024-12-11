import time
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from ..config import settings
import httpx

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"

# Cache variables
cache = None
cache_time = 0
CACHE_EXPIRATION = 86400  # 24 hours in seconds

@router.get(base_api_url + "locations")
async def get_locations():
    """Return a list of available locations"""
    global cache, cache_time

    # Check if cache is still valid
    if cache is not None and (time.time() - cache_time) < CACHE_EXPIRATION:
        return cache

    locations_url = 'https://api.bron.live/locations/search?includes=id,name,kind&limit=999'
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(locations_url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()

            # Data structure:
            # data['hits']['hits'] is an array of items. Each item has '_source': {'id', 'kind', 'name'}
            hits = data.get('hits', {}).get('hits', [])

            # Transform the data into the desired format
            items = []
            for hit in hits:
                source = hit.get('_source', {})
                
                # Check if 'id' key exists in the source
                if 'id' not in source:
                    logger.warning('Missing expected key "id" in source: %s', source)
                    continue  # Skip this item if 'id' is missing

                # Skip items where id contains 'type:' or '*'
                if 'type:' in source['id'] or '*' in source['id']:
                    continue

                # Use get to safely access 'kind'
                kind = source.get('kind', 'Ministerie')  # Default to 'Ministerie' if 'kind' is not present

                # Map the kind to the desired format
                if kind == 'municipality':
                    kind_label = 'Gemeente'
                elif kind == 'province':
                    kind_label = 'Provincie'
                    
                items.append({
                    'value': source['id'],
                    'label': source.get('name', 'Unnamed'),  # Default to 'Unnamed' if 'name' is not present
                    'group': kind_label
                })

            locations = items
            # Update cache
            cache = locations
            cache_time = time.time()
            
    except httpx.HTTPStatusError as http_error:
        logger.error('HTTP error occurred: %s', http_error)
        raise HTTPException(
            status_code=http_error.response.status_code,
            detail=f"HTTP error occurred: {http_error.response.text}"
        )
    except httpx.RequestError as request_error:
        logger.error('Request error occurred: %s', request_error)
        raise HTTPException(
            status_code=500,
            detail="Error occurred while making the request to the external API."
        )
    except Exception as error:
        logger.error('Unexpected error occurred: %s', error)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request."
        )

    return locations
    