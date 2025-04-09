import os
import sys
import traceback
from simplified_app import app, load_evictions, EVICTIONS_DB, create_sample_data_without_flash

def setup_environment():
    """Set up the environment and data"""
    print("Setting up environment...")
    
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('eviction_data', exist_ok=True)
    
    # Create sample data if no evictions exist
    load_evictions()
    if not EVICTIONS_DB:
        try:
            create_sample_data_without_flash()
            print("Created sample eviction data")
        except Exception as e:
            print(f"Error creating sample data: {e}")
            traceback.print_exc()
    else:
        print(f"Loaded {len(EVICTIONS_DB)} existing eviction records")

if __name__ == "__main__":
    try:
        setup_environment()
        
        # Run the app with debugging
        print("\n" + "=" * 60)
        print("Eviction Management System Starting")
        print("=" * 60)
        print("Access the application at http://localhost:5000")
        print("Use Ctrl+C to stop the server")
        print("=" * 60 + "\n")
        
        # Register error handler for unhandled exceptions
        @app.errorhandler(Exception)
        def handle_exception(e):
            app.logger.error(f"Unhandled exception: {str(e)}")
            traceback.print_exc()
            return "An error occurred. Check the server logs for details.", 500
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc() 