import os
import json
from datetime import datetime, timedelta
import pandas as pd

# Create necessary directories
os.makedirs('reports', exist_ok=True)
os.makedirs('eviction_data', exist_ok=True)

# Define average timelines for eviction process (in days)
AVERAGE_TIMELINES = {
    'filing_to_service': 5,
    'service_to_court': 14,
    'court_to_judgment': 2,
    'judgment_to_writ': 7,
    'writ_to_eviction': 7
}

# Load evictions
def load_evictions():
    try:
        if os.path.exists('eviction_data/evictions.json'):
            with open('eviction_data/evictions.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading evictions: {e}")
    return []

def calculate_timeline_from_writ_date(writ_date_str):
    """Calculate timeline if writ filed on given date"""
    writ_date = datetime.strptime(writ_date_str, '%Y-%m-%d')
    
    # From writ date, we can calculate eviction date (forward)
    eviction_date = writ_date + timedelta(days=AVERAGE_TIMELINES['writ_to_eviction'])
    
    # We can also calculate judgment date (backward)
    judgment_date = writ_date - timedelta(days=AVERAGE_TIMELINES['judgment_to_writ'])
    
    # Court date (backward)
    court_date = judgment_date - timedelta(days=AVERAGE_TIMELINES['court_to_judgment'])
    
    # Service date (backward)
    service_date = court_date - timedelta(days=AVERAGE_TIMELINES['service_to_court'])
    
    # Filing date (backward)
    filing_date = service_date - timedelta(days=AVERAGE_TIMELINES['filing_to_service'])
    
    # Days to eviction from now
    days_to_eviction = (eviction_date - datetime.now()).days
    
    return {
        'filing_date': filing_date.strftime('%Y-%m-%d'),
        'service_date': service_date.strftime('%Y-%m-%d'),
        'court_date': court_date.strftime('%Y-%m-%d'),
        'judgment_date': judgment_date.strftime('%Y-%m-%d'),
        'writ_date': writ_date.strftime('%Y-%m-%d'),
        'eviction_date': eviction_date.strftime('%Y-%m-%d'),
        'days_to_eviction': max(0, days_to_eviction)
    }

def generate_report():
    # Load evictions data
    evictions = load_evictions()
    
    if not evictions:
        print("No eviction data found. Please run the application first to import data.")
        return
    
    # Filter for Fulton County (assumes there's a county field, or we extract from address)
    fulton_evictions = []
    for eviction in evictions:
        property_address = eviction.get('property_address', '').lower()
        # Check if address contains Fulton County or is in Atlanta (simplified logic)
        if 'fulton' in property_address or 'atlanta, ga' in property_address:
            fulton_evictions.append(eviction)
    
    # Sort by filing date (newest first)
    try:
        sorted_evictions = sorted(
            fulton_evictions, 
            key=lambda x: datetime.strptime(x.get('filing_date', '1900-01-01'), '%Y-%m-%d'),
            reverse=True
        )
    except ValueError:
        print("Error parsing dates. Using unsorted data.")
        sorted_evictions = fulton_evictions
    
    # Get the last 20 evictions (or all if less than 20)
    last_20_evictions = sorted_evictions[:20]
    
    # Calculate timeline for writ filed today
    today = datetime.now().strftime('%Y-%m-%d')
    timeline = calculate_timeline_from_writ_date(today)
    
    # Generate report
    report_name = f"fulton_county_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report_path_json = os.path.join('reports', f"{report_name}.json")
    report_path_md = os.path.join('reports', f"{report_name}.md")
    
    # Create report data
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'title': 'Fulton County Eviction Report',
        'eviction_count': len(last_20_evictions),
        'evictions': last_20_evictions,
        'writ_timeline': timeline
    }
    
    # Save JSON report
    with open(report_path_json, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Create Markdown report
    with open(report_path_md, 'w') as f:
        f.write(f"# Fulton County Eviction Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Timeline for Writ Filed Today\n\n")
        f.write(f"If a writ is filed today ({today}), the expected timeline is:\n\n")
        f.write(f"- **Filing Date (historical)**: {timeline['filing_date']}\n")
        f.write(f"- **Service Date (historical)**: {timeline['service_date']}\n")
        f.write(f"- **Court Date (historical)**: {timeline['court_date']}\n")
        f.write(f"- **Judgment Date (historical)**: {timeline['judgment_date']}\n")
        f.write(f"- **Writ Date (today)**: {timeline['writ_date']}\n")
        f.write(f"- **Expected Eviction Date**: {timeline['eviction_date']}\n")
        f.write(f"- **Days Until Eviction**: {timeline['days_to_eviction']}\n\n")
        
        f.write("## Last 20 Evictions in Fulton County\n\n")
        
        if last_20_evictions:
            f.write("| Case # | Tenant | Property | Filing Date | Status | Judgment Amount |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            for eviction in last_20_evictions:
                case_number = eviction.get('case_number', 'Unknown')
                tenant_name = eviction.get('tenant_name', 'Unknown')
                property_address = eviction.get('property_address', 'Unknown')
                filing_date = eviction.get('filing_date', 'Unknown')
                status = eviction.get('status', 'Unknown')
                judgment_amount = f"${eviction.get('judgment_amount', 'N/A')}" if eviction.get('judgment_amount') else 'N/A'
                
                f.write(f"| {case_number} | {tenant_name} | {property_address} | {filing_date} | {status} | {judgment_amount} |\n")
        else:
            f.write("No evictions found in Fulton County.\n")
    
    print(f"Report generated successfully!")
    print(f"JSON report saved to: {report_path_json}")
    print(f"Markdown report saved to: {report_path_md}")
    
    # Display the timeline in the console
    print("\nTimeline Summary if Writ Filed Today:")
    print(f"Expected Eviction Date: {timeline['eviction_date']}")
    print(f"Days Until Eviction: {timeline['days_to_eviction']}")

if __name__ == "__main__":
    generate_report() 