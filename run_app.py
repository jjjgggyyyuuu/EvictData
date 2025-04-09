import os
from simplified_app import app, load_evictions, EVICTIONS_DB, save_evictions, create_sample_data_without_flash

if __name__ == '__main__':
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('eviction_data', exist_ok=True)
    
    # Create sample data if no evictions exist
    load_evictions()
    if not EVICTIONS_DB:
        create_sample_data_without_flash()
        print("Created sample eviction data")
    else:
        print(f"Loaded {len(EVICTIONS_DB)} existing eviction records")
    
    # Run the app
    print("\n" + "=" * 60)
    print("Eviction Management System Starting")
    print("=" * 60)
    print("Access the application at http://localhost:5000")
    print("Use Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 