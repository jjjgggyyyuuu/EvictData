import os
import json
from datetime import datetime, timedelta
import random

# Load existing evictions
def load_evictions():
    try:
        if os.path.exists('eviction_data/evictions.json'):
            with open('eviction_data/evictions.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading evictions: {e}")
    return []

# Save evictions to file
def save_evictions(evictions):
    try:
        os.makedirs('eviction_data', exist_ok=True)
        with open('eviction_data/evictions.json', 'w') as f:
            json.dump(evictions, f, indent=2, default=str)
        print(f"Saved {len(evictions)} eviction records")
    except Exception as e:
        print(f"Error saving evictions: {e}")

# Generate unique ID for evictions
def generate_id():
    return str(datetime.now().timestamp() + random.random()).replace('.', '')

def add_fulton_county_data():
    # Load existing data
    evictions = load_evictions()
    
    # Atlanta neighborhoods in Fulton County
    neighborhoods = [
        "Buckhead", "Midtown", "Downtown", "Old Fourth Ward", "West End", 
        "East Atlanta", "Virginia Highland", "Inman Park", "Grant Park", "Peachtree Hills"
    ]
    
    # Fulton County streets
    streets = [
        "Peachtree St", "Piedmont Ave", "Ponce de Leon Ave", "North Ave", "10th St",
        "Cascade Rd", "Roswell Rd", "Howell Mill Rd", "Metropolitan Pkwy", "Martin Luther King Jr Dr"
    ]
    
    # Tenant names
    first_names = [
        "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", 
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
        "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"
    ]
    
    # Generate 25 Fulton County evictions
    today = datetime.now()
    fulton_evictions = []
    
    for i in range(25):
        # Generate random filing date within last 120 days
        days_ago = random.randint(1, 120)
        filing_date = today - timedelta(days=days_ago)
        
        # Determine status based on filing date
        if days_ago < 7:
            status = 'pending'
            judgment_amount = None
            judgment_date = None
            writ_date = None
        elif days_ago < 20:
            status = 'active'
            judgment_amount = None
            judgment_date = None
            writ_date = None
        elif days_ago < 35:
            status = 'judgment'
            judgment_amount = round(random.uniform(2000, 7000), 2)
            judgment_date = (filing_date + timedelta(days=random.randint(14, 21))).strftime('%Y-%m-%d')
            writ_date = None
        elif days_ago < 50:
            status = 'writ'
            judgment_amount = round(random.uniform(2000, 7000), 2)
            judgment_date = (filing_date + timedelta(days=random.randint(14, 21))).strftime('%Y-%m-%d')
            writ_date = (filing_date + timedelta(days=random.randint(22, 30))).strftime('%Y-%m-%d')
        else:
            status = 'completed'
            judgment_amount = round(random.uniform(2000, 7000), 2)
            judgment_date = (filing_date + timedelta(days=random.randint(14, 21))).strftime('%Y-%m-%d')
            writ_date = (filing_date + timedelta(days=random.randint(22, 30))).strftime('%Y-%m-%d')
        
        # Generate random address in Fulton County
        street_num = random.randint(100, 9999)
        street = random.choice(streets)
        unit = f"Apt {random.randint(1, 20)}{random.choice(['A', 'B', 'C', ''])}"
        neighborhood = random.choice(neighborhoods)
        address = f"{street_num} {street}, {unit}, {neighborhood}, Atlanta, GA 30303, Fulton County"
        
        # Generate tenant name
        tenant_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Create eviction record
        eviction = {
            'id': generate_id(),
            'case_number': f"EV-FC-{2025}-{1000 + i}",
            'tenant_name': tenant_name,
            'property_address': address,
            'filing_date': filing_date.strftime('%Y-%m-%d'),
            'status': status,
            'judgment_amount': judgment_amount,
            'judgment_date': judgment_date,
            'writ_date': writ_date,
            'days_to_eviction': random.randint(0, 35) if status != 'completed' else 0
        }
        
        fulton_evictions.append(eviction)
    
    # Add to existing evictions
    evictions.extend(fulton_evictions)
    
    # Save updated database
    save_evictions(evictions)
    print(f"Added {len(fulton_evictions)} Fulton County evictions")

if __name__ == "__main__":
    add_fulton_county_data() 