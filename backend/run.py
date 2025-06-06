
#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import flask
        import requests
        import boto3
        import prometheus_client
        print("✅ All Python dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def setup_database():
    """Initialize database tables"""
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_prometheus():
    """Check if Prometheus services are available"""
    try:
        import requests
        
        # Check Prometheus
        try:
            response = requests.get("http://localhost:9090/-/healthy", timeout=2)
            if response.status_code == 200:
                print("✅ Prometheus is running")
            else:
                print("⚠️  Prometheus not healthy")
        except:
            print("⚠️  Prometheus not available (will use mock mode)")
        
        # Check Pushgateway
        try:
            response = requests.get("http://localhost:9091/metrics", timeout=2)
            if response.status_code == 200:
                print("✅ Pushgateway is running")
            else:
                print("⚠️  Pushgateway not healthy")
        except:
            print("⚠️  Pushgateway not available (will use mock mode)")
        
        return True
    except Exception as e:
        print(f"⚠️  Prometheus check failed: {e}")
        return True  # Non-blocking

def start_services():
    """Start all required services"""
    print("🚀 Starting AA Gateway AI Operations...")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Setup database
    if not setup_database():
        return False
    
    # Check Prometheus (non-blocking)
    check_prometheus()
    
    # Start Flask app
    print("🌟 Starting Flask application...")
    from app import app
    
    # Enable debug mode for development
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
    
    return True

def start_with_docker():
    """Start services using Docker Compose"""
    print("🐳 Starting with Docker Compose...")
    
    if not Path("docker-compose.yml").exists():
        print("❌ docker-compose.yml not found")
        return False
    
    try:
        # Build and start services
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        print("✅ Docker services started")
        
        # Wait for services to be ready
        time.sleep(10)
        
        # Check service health
        subprocess.run(["docker-compose", "ps"], check=True)
        
        print("\n🌟 Services started successfully!")
        print("📊 Dashboard: http://localhost:5000")
        print("📈 Prometheus: http://localhost:9090")
        print("📊 Grafana: http://localhost:3000 (admin/admin123)")
        print("\n💡 Run 'docker-compose logs -f' to see logs")
        print("💡 Run 'docker-compose down' to stop services")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker Compose failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose not installed")
        print("💡 Install Docker and Docker Compose first")
        return False

def main():
    """Main entry point"""
    print("🤖 AA Gateway AI Operations - Setup & Launch")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "docker":
        success = start_with_docker()
    else:
        success = start_services()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()