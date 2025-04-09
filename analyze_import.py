import csv_import_tools as cit
import json

def main():
    csv_path = r'C:\Users\Jorda\Downloads\SearchExport_Cases_638797223707338702.csv'
    print("Analyzing CSV file...")
    inspection = cit.inspect_csv(csv_path)
    print("\nFile Analysis:")
    print(json.dumps(inspection, indent=2))
    
    print("\nSuggesting column mappings...")
    mappings = cit.suggest_column_mapping(inspection)
    print("\nColumn Mappings:")
    print(json.dumps(mappings, indent=2))
    
    print("\nPreviewing import...")
    preview = cit.preview_import(csv_path, mappings)
    print("\nImport Preview:")
    print(json.dumps(preview, indent=2))

if __name__ == '__main__':
    main() 