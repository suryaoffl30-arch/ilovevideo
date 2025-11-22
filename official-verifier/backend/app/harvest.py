"""CLI tool for running harvesters."""
import asyncio
import sys
from uuid import UUID

from app.db.base import db
from app.db.repository import repository
from app.services.harvester import harvest_entity, normalize_and_extract_domain
from app.services.scoring import SIGNAL_PRESETS


async def harvest_and_process(entity_name: str, entity_id: UUID = None):
    """
    Harvest data for an entity and process results.
    
    Args:
        entity_name: Name of the entity to harvest
        entity_id: Optional existing entity ID
    """
    print(f"Harvesting data for: {entity_name}")
    
    # Harvest from all sources
    results = await harvest_entity(entity_name)
    
    print(f"Found {len(results.get('wikipedia', []))} Wikipedia URLs")
    print(f"Found {len(results.get('appstore', []))} App Store URLs")
    print(f"Found {len(results.get('playstore', []))} Play Store URLs")
    
    # Create or get entity
    if not entity_id:
        entity_id = await repository.upsert_entity(entity_name)
        print(f"Created entity: {entity_id}")
    
    # Process each source
    for source_type, urls in results.items():
        if not urls:
            continue
        
        # Get signal preset
        preset = SIGNAL_PRESETS.get(source_type)
        if not preset:
            print(f"Warning: No preset for {source_type}")
            continue
        
        score_contrib, weight = preset
        
        for url in urls:
            # Extract domain
            domain = normalize_and_extract_domain(url)
            if not domain:
                continue
            
            print(f"Processing {source_type}: {url} -> {domain}")
            
            # Upsert domain
            domain_id = await repository.upsert_domain(entity_id, domain, is_primary=False)
            
            # Upsert source
            source_id = await repository.upsert_source(source_type, url, source_type.title())
            
            # Create verification
            await repository.create_verification(
                entity_id,
                source_id,
                score_contrib,
                weight,
                domain_id,
                {'harvested_url': url}
            )
    
    # Recompute score
    new_score = await repository.recompute_entity_score(entity_id)
    print(f"Updated confidence score: {new_score}")
    
    return entity_id


async def run_once():
    """Run harvester once for testing."""
    await db.connect()
    
    try:
        # Example: Harvest HDFC Bank
        entity_id = await harvest_and_process("HDFC Bank")
        print(f"Completed harvest for entity: {entity_id}")
    
    finally:
        await db.disconnect()


async def run_scheduled():
    """Run harvester on a schedule."""
    # TODO: Implement scheduled harvesting
    # Could use APScheduler or similar
    pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_once":
        asyncio.run(run_once())
    else:
        print("Usage: python -m app.harvest run_once")
        sys.exit(1)
