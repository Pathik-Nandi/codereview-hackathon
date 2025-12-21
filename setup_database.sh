#!/bin/bash

###############################################################################
# Database Setup Script for PR Analysis System
# 
# This script creates all necessary database tables for the PR review system
# 
# Usage:
#   ./setup_database.sh
#
# Prerequisites:
#   - PostgreSQL server running
#   - Python 3.8+ installed
#   - Required Python packages installed (from requirements.txt)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

###############################################################################
# Load Environment Variables
###############################################################################

load_env() {
    print_info "Loading environment variables from .env file..."
    
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_error ".env file not found!"
        print_info "Please create a .env file with database configuration."
        exit 1
    fi
    
    # Load .env file
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    
    print_success "Environment variables loaded"
}

###############################################################################
# Verify Prerequisites
###############################################################################

verify_prerequisites() {
    print_header "Verifying Prerequisites"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Check if PostgreSQL is accessible
    print_info "Checking PostgreSQL connection..."
    
    if command -v psql &> /dev/null; then
        print_success "psql command found"
    else
        print_warning "psql command not found (optional)"
    fi
    
    # Check required Python packages
    print_info "Checking required Python packages..."
    
    if python3 -c "import sqlalchemy" 2>/dev/null; then
        print_success "SQLAlchemy is installed"
    else
        print_error "SQLAlchemy is not installed"
        print_info "Run: pip3 install -r requirements.txt"
        exit 1
    fi
    
    if python3 -c "import psycopg2" 2>/dev/null; then
        print_success "psycopg2 is installed"
    else
        print_error "psycopg2 is not installed"
        print_info "Run: pip3 install -r requirements.txt"
        exit 1
    fi
}

###############################################################################
# Database Connection Test
###############################################################################

test_database_connection() {
    print_header "Testing Database Connection"
    
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-pr_analysis}
    DB_USER=${DB_USER:-postgres}
    
    print_info "Database: $DB_NAME"
    print_info "Host: $DB_HOST"
    print_info "Port: $DB_PORT"
    print_info "User: $DB_USER"
    
    # Test connection using Python
    python3 << EOF
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

try:
    connection_string = "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    engine = create_engine(connection_string, echo=False)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        version = result.fetchone()[0]
        print(f"✓ Connected to: {version.split(',')[0]}")
    
    sys.exit(0)
except SQLAlchemyError as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed"
        print_info "Please check your database configuration in .env file"
        exit 1
    fi
}

###############################################################################
# Create Database (if not exists)
###############################################################################

create_database_if_not_exists() {
    print_header "Checking Database Existence"
    
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-pr_analysis}
    DB_USER=${DB_USER:-postgres}
    
    python3 << EOF
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

try:
    # Connect to postgres database to check if target database exists
    admin_connection_string = "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/postgres"
    admin_engine = create_engine(admin_connection_string, isolation_level="AUTOCOMMIT", echo=False)
    
    with admin_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": "${DB_NAME}"}
        )
        exists = result.fetchone() is not None
        
        if exists:
            print(f"✓ Database '${DB_NAME}' already exists")
        else:
            print(f"ℹ Database '${DB_NAME}' does not exist, creating...")
            conn.execute(text(f"CREATE DATABASE ${DB_NAME}"))
            print(f"✓ Database '${DB_NAME}' created successfully")
    
    sys.exit(0)
except OperationalError as e:
    if "does not exist" in str(e):
        print(f"⚠ Could not create database. Please create it manually:")
        print(f"  CREATE DATABASE ${DB_NAME};")
    else:
        print(f"✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        print_warning "Failed to create database automatically"
        print_info "Please ensure the database exists before continuing"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

###############################################################################
# Create Tables
###############################################################################

create_tables() {
    print_header "Creating Database Tables"
    
    print_info "Running table creation script..."
    
    cd "$SCRIPT_DIR"
    
    # Run the Python script to create tables
    python3 << 'EOF'
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from models.database import Base
import os

try:
    # Build connection string from environment variables
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'pr_analysis')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"Creating tables in database: {db_name}")
    
    engine = create_engine(connection_string, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # List created tables
    table_names = sorted(Base.metadata.tables.keys())
    print(f"\n✓ Successfully created {len(table_names)} tables:")
    for table_name in table_names:
        print(f"  • {table_name}")
    
    # Show table details
    print("\nTable Descriptions:")
    print("-" * 60)
    
    tables_info = {
        'pr_analysis': 'Main table for PR analysis results',
        'pr_issues': 'Individual issues found in PR analysis',
        'pr_metrics': 'Detailed code metrics for each PR',
        'user_statistics': 'Aggregated user performance statistics',
        'best_practices': 'Best practice recommendations',
        'user_analytics': 'User analytics snapshots over time',
        'users': 'User authentication and profile information',
        'user_sessions': 'Active user login sessions with JWT tokens'
    }
    
    for table_name, description in tables_info.items():
        if table_name in table_names:
            print(f"  {table_name:25} - {description}")
    
    sys.exit(0)
    
except SQLAlchemyError as e:
    print(f"\n✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(2)
EOF

    if [ $? -eq 0 ]; then
        print_success "All tables created successfully!"
    else
        print_error "Table creation failed"
        exit 1
    fi
}

###############################################################################
# Verify Tables
###############################################################################

verify_tables() {
    print_header "Verifying Table Creation"
    
    python3 << 'EOF'
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import os

try:
    # Build connection string
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'pr_analysis')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string, echo=False)
    
    # Get table information
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        print("✗ No tables found in database")
        sys.exit(1)
    
    print(f"✓ Found {len(tables)} tables in database")
    
    # Verify expected tables exist
    expected_tables = [
        'pr_analysis', 'pr_issues', 'pr_metrics', 
        'user_statistics', 'best_practices', 'user_analytics'
    ]
    
    missing_tables = [t for t in expected_tables if t not in tables]
    
    if missing_tables:
        print(f"\n⚠ Missing tables: {', '.join(missing_tables)}")
    else:
        print(f"✓ All expected tables are present")
    
    # Show table row counts
    print("\nTable Row Counts:")
    with engine.connect() as conn:
        for table in sorted(tables):
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table:25} {count:>10} rows")
            except Exception as e:
                print(f"  {table:25} {'ERROR':>10}")
    
    sys.exit(0)
    
except SQLAlchemyError as e:
    print(f"\n✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_success "Table verification complete"
    else
        print_error "Table verification failed"
        exit 1
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    print_header "PR Analysis System - Database Setup"
    echo ""
    
    # Step 1: Load environment
    load_env
    echo ""
    
    # Step 2: Verify prerequisites
    verify_prerequisites
    echo ""
    
    # Step 3: Test database connection
    test_database_connection
    echo ""
    
    # Step 4: Create database if needed
    create_database_if_not_exists
    echo ""
    
    # Step 5: Create tables
    create_tables
    echo ""
    
    # Step 6: Verify tables
    verify_tables
    echo ""
    
    # Success message
    print_header "Setup Complete!"
    print_success "Database setup completed successfully!"
    print_info "You can now run the application with: python3 main.py"
    echo ""
}

# Run main function
main
