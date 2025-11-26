import json
from datetime import datetime
from DatabaseService import DatabaseService

def import_wahlsprueche_from_json(json_filepath: str, use_postgres: bool = False):
    """
    Imports Wahlsprüche from a JSON file into the database.
    
    Args:
        json_filepath: Path to the JSON file
        use_postgres: Whether to use PostgreSQL (True) or SQLite (False)
    
    Returns:
        Dictionary with statistics about the import
    """
    # Load JSON file
    with open(json_filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Get database environment
    env = DatabaseService.get_sillyorm_environment(use_postgres=use_postgres)
    
    # Statistics
    stats = {
        'total': 0,
        'created': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Process each Wahlspruch
    for item in data['wahlsprueche']:
        stats['total'] += 1
        
        # Parse the dictionary (key is the Spruch, value is the metadata)
        for spruch, metadata in item.items():
            try:
                # Parse metadata: "Partei, Wahl, Datum"
                parts = metadata.split(', ')
                
                partei = parts[0] if len(parts) > 0 else None
                wahl = parts[1] if len(parts) > 1 else None
                datum_str = parts[2] if len(parts) > 2 else None
                
                # Convert date string to date object
                datum = None
                if datum_str:
                    try:
                        datum = datetime.strptime(datum_str, "%d.%m.%Y").date()
                    except ValueError:
                        print(f"Warning: Could not parse date '{datum_str}' for spruch '{spruch[:50]}...'")
                
                # Create Wahlspruch
                success = DatabaseService.create_new_wahlspruch(
                    env=env,
                    text=spruch,
                    partei=partei,
                    wahl=wahl,
                    datum=datum,
                    quelle=None  # No source information in JSON
                )
                
                if success:
                    stats['created'] += 1
                    print(f"✓ Created: {spruch[:50]}...")
                else:
                    stats['skipped'] += 1
                    print(f"⊘ Skipped (already exists): {spruch[:50]}...")
                    
            except Exception as e:
                stats['errors'] += 1
                print(f"✗ Error processing '{spruch[:50]}...': {str(e)}")
    
    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total entries:     {stats['total']}")
    print(f"Created:           {stats['created']}")
    print(f"Skipped:           {stats['skipped']}")
    print(f"Errors:            {stats['errors']}")
    print("="*60)
    
    return stats


if __name__ == "__main__":
    # Example usage
    json_file = r"C:\Users\loris\Desktop\Coding\WahlplakatGame\Docs\wahlsprüche.json"  # Change this to your JSON file path
    
    # Import to SQLite (default)
    print("Importing to SQLite...")
    import_wahlsprueche_from_json(json_file, use_postgres=True)
    
    # Or import to PostgreSQL
    # print("Importing to PostgreSQL...")
    # import_wahlsprueche_from_json(json_file, use_postgres=True)