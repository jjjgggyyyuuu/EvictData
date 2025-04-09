import pandas as pd
import os
import json
from datetime import datetime
import re
from pathlib import Path

class EvictionDataImporter:
    def __init__(self, db_connection=None):
        """Initialize the importer with an optional database connection"""
        self.db_connection = db_connection
        self.export_dir = Path("eviction_data")
        # Create export directory if it doesn't exist
        if not self.export_dir.exists():
            self.export_dir.mkdir(parents=True)
            
    def clean_text(self, text):
        """Clean and normalize text from the CSV"""
        if pd.isna(text):
            return ""
        
        # Replace HTML encoded characters
        text = text.replace("&#x2F;", "/")
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def parse_date(self, date_str):
        """Parse dates in expected formats"""
        if pd.isna(date_str):
            return None
            
        try:
            # Try common formats
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%B %d, %Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # Failed to parse
            print(f"Warning: Could not parse date '{date_str}'")
            return None
        except Exception as e:
            print(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def extract_parties(self, case_description):
        """Extract plaintiff and defendant from case description"""
        if pd.isna(case_description):
            return {"plaintiff": "", "defendants": []}
            
        # Clean up case description
        case_description = self.clean_text(case_description)
        
        # Try to split on 'vs.' or 'v.'
        vs_pattern = r'\s+(?:vs\.|v\.)\s+'
        parts = re.split(vs_pattern, case_description, maxsplit=1)
        
        if len(parts) == 2:
            plaintiff = parts[0].strip()
            defendants_str = parts[1].strip()
            
            # Split defendants
            defendants = []
            for defendant in re.split(r',|\\n', defendants_str):
                defendant = defendant.strip()
                if defendant and not defendant.lower().startswith('all other'):
                    defendants.append(defendant)
            
            return {
                "plaintiff": plaintiff,
                "defendants": defendants
            }
        else:
            # No vs. pattern found
            return {
                "plaintiff": case_description,
                "defendants": []
            }
    
    def extract_eviction_status(self, content_text):
        """Extract eviction status from content text"""
        if pd.isna(content_text):
            return "unknown"
            
        content = self.clean_text(content_text).lower()
        
        status = {
            "vacated": "VACATED" in content_text,
            "ejected": "EJECTED" in content_text,
            "settled": "SETTLED" in content_text,
            "held_up": "HELD UP" in content_text,
            "pending": True  # Default to pending unless we know otherwise
        }
        
        # Determine most specific status
        if status["vacated"]:
            return "vacated"
        elif status["ejected"]:
            return "ejected"
        elif status["settled"]:
            return "settled"
        elif status["held_up"]:
            return "held_up"
        else:
            return "pending"
    
    def import_csv(self, file_path):
        """Import and process the eviction CSV data"""
        try:
            print(f"Importing data from {file_path}...")
            df = pd.read_csv(file_path)
            
            # Check if the file has the expected structure
            expected_columns = ["File Date", "Case Description", "Case Number", 
                               "Filing Code", "Document Name", "Pages", "Content Text"]
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                print(f"Warning: CSV is missing expected columns: {missing_columns}")
                return None
                
            # Process data
            eviction_cases = []
            
            for _, row in df.iterrows():
                # Extract core data
                file_date = self.parse_date(row["File Date"])
                case_number = row["Case Number"] if not pd.isna(row["Case Number"]) else ""
                filing_code = row["Filing Code"] if not pd.isna(row["Filing Code"]) else ""
                document_name = row["Document Name"] if not pd.isna(row["Document Name"]) else ""
                
                # Process parties
                parties = self.extract_parties(row["Case Description"])
                
                # Process status
                status = self.extract_eviction_status(row["Content Text"])
                
                # Create case record
                case = {
                    "case_number": case_number.strip(),
                    "file_date": file_date.isoformat() if file_date else None,
                    "plaintiff": parties["plaintiff"],
                    "defendants": parties["defendants"],
                    "filing_code": filing_code.strip(),
                    "document_name": document_name.strip(),
                    "status": status,
                    "imported_at": datetime.now().isoformat()
                }
                
                eviction_cases.append(case)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"eviction_cases_{timestamp}.json"
            
            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(eviction_cases, f, indent=2)
                
            print(f"Successfully imported {len(eviction_cases)} eviction cases")
            print(f"Data saved to {output_file}")
            
            return eviction_cases
            
        except Exception as e:
            print(f"Error importing CSV: {str(e)}")
            return None

if __name__ == "__main__":
    # Get file path from user
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("Please specify the CSV file path:")
        file_path = input("> ")
    
    importer = EvictionDataImporter()
    importer.import_csv(file_path) 