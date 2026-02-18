#!/usr/bin/env python3
"""
One-time setup script for Azure PostgreSQL RAG Integration.
Provisions PostgreSQL Flexible Server, enables pgvector, and creates schema.

Steps covered:
1. Provision Azure PostgreSQL Flexible Server (via Azure CLI)
2. Configure pgvector Extension
3. Create Schema

Prerequisites:
- Azure CLI installed and logged in (az login)
- Python 3.10+
- Required packages: asyncpg, python-dotenv
"""

import os
import sys
import subprocess
import json
import asyncio
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Default configuration
DEFAULT_CONFIG = {
    "resource_group": "workbenchiq-rg",
    "server_name": "workbenchiq-db",
    "location": "westus2",
    "admin_user": "workbenchiq_admin",
    "sku_name": "Standard_B2ms",
    "tier": "Burstable",  # Burstable for dev, GeneralPurpose for prod
    "storage_size": 32,
    "postgres_version": "15",
    "database_name": "workbenchiq",
    "schema_name": "workbenchiq",
}

# Schema SQL for creating tables
SCHEMA_SQL = """
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create schema
CREATE SCHEMA IF NOT EXISTS {schema_name};
SET search_path TO {schema_name}, public;

-- Policy chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS policy_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
        'policy_header',
        'criteria',
        'modifying_factor',
        'reference',
        'description'
    )),
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    criteria_id VARCHAR(50),
    risk_level VARCHAR(30),
    action_recommendation TEXT,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    metadata JSONB DEFAULT '{{}}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create unique index for upsert operations (must be index, not constraint, due to COALESCE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_policy_chunks_unique ON policy_chunks 
    (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

-- Create HNSW index for fast vector search
CREATE INDEX IF NOT EXISTS idx_policy_chunks_embedding ON policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Additional indexes for filtering
CREATE INDEX IF NOT EXISTS idx_policy_chunks_category ON policy_chunks (category);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_subcategory ON policy_chunks (subcategory);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_policy_id ON policy_chunks (policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_risk_level ON policy_chunks (risk_level);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_chunk_type ON policy_chunks (chunk_type);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_metadata ON policy_chunks USING gin (metadata);

-- Full-text search index for hybrid search
CREATE INDEX IF NOT EXISTS idx_policy_chunks_content_trgm ON policy_chunks 
    USING gin (content gin_trgm_ops);

-- Verify setup
SELECT 'pgvector extension enabled' as status WHERE EXISTS (
    SELECT 1 FROM pg_extension WHERE extname = 'vector'
);
"""


def run_az_command(args: list[str], capture_output: bool = True) -> tuple[bool, str]:
    """Run an Azure CLI command and return success status and output."""
    # On Windows, use 'az.cmd' or run through shell
    cmd = ["az"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False,
            shell=True  # Required for Windows to find 'az' in PATH
        )
        if result.returncode == 0:
            return True, result.stdout.strip() if capture_output else ""
        else:
            error_msg = result.stderr.strip() if capture_output else ""
            # Also check stdout for error messages (az sometimes outputs errors there)
            if not error_msg and result.stdout:
                error_msg = result.stdout.strip()
            return False, error_msg
    except FileNotFoundError:
        return False, "Azure CLI (az) not found. Please install it first."
    except Exception as e:
        return False, str(e)


def check_az_login() -> bool:
    """Check if Azure CLI is logged in."""
    success, output = run_az_command(["account", "show", "--output", "json"])
    if success:
        try:
            account = json.loads(output)
            print(f"✅ Logged in to Azure as: {account.get('user', {}).get('name', 'Unknown')}")
            print(f"   Subscription: {account.get('name', 'Unknown')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Azure CLI output: {e}")
            print(f"   Output was: {output[:200] if output else '(empty)'}")
            return False
    else:
        if "az login" in output.lower() or "not logged in" in output.lower():
            print("❌ Not logged in to Azure CLI. Please run: az login")
        else:
            print(f"❌ Azure CLI error: {output}")
        return False


def check_resource_group(resource_group: str) -> bool:
    """Check if resource group exists."""
    success, _ = run_az_command(["group", "show", "--name", resource_group])
    return success


def create_resource_group(resource_group: str, location: str) -> bool:
    """Create a resource group."""
    print(f"⏳ Creating resource group '{resource_group}' in {location}...")
    success, output = run_az_command([
        "group", "create",
        "--name", resource_group,
        "--location", location
    ])
    if success:
        print(f"✅ Resource group '{resource_group}' created")
        return True
    else:
        print(f"❌ Failed to create resource group: {output}")
        return False


def check_server_exists(resource_group: str, server_name: str) -> bool:
    """Check if PostgreSQL server already exists."""
    success, _ = run_az_command([
        "postgres", "flexible-server", "show",
        "--resource-group", resource_group,
        "--name", server_name
    ])
    return success


def provision_postgresql_server(config: dict, admin_password: str) -> bool:
    """
    Step 1: Provision Azure PostgreSQL Flexible Server.
    """
    print("\n" + "=" * 60)
    print("Step 1: Provision Azure PostgreSQL Flexible Server")
    print("=" * 60)
    
    # Check if server already exists
    if check_server_exists(config["resource_group"], config["server_name"]):
        print(f"✅ Server '{config['server_name']}' already exists")
        return True
    
    print(f"\n⏳ Creating PostgreSQL Flexible Server (this may take 5-10 minutes)...")
    print(f"   Server: {config['server_name']}")
    print(f"   Resource Group: {config['resource_group']}")
    print(f"   Location: {config['location']}")
    print(f"   SKU: {config['sku_name']}")
    print(f"   PostgreSQL Version: {config['postgres_version']}")
    
    success, output = run_az_command([
        "postgres", "flexible-server", "create",
        "--resource-group", config["resource_group"],
        "--name", config["server_name"],
        "--location", config["location"],
        "--admin-user", config["admin_user"],
        "--admin-password", admin_password,
        "--sku-name", config["sku_name"],
        "--tier", config.get("tier", "Burstable"),
        "--storage-size", str(config["storage_size"]),
        "--version", config["postgres_version"],
        "--public-access", "0.0.0.0-255.255.255.255",  # Allow all for dev
        "--yes"  # Skip confirmation prompts
    ])
    
    if success:
        print(f"✅ PostgreSQL server '{config['server_name']}' created successfully")
        return True
    else:
        print(f"❌ Failed to create PostgreSQL server: {output}")
        return False


def enable_pgvector_extension(config: dict) -> bool:
    """
    Step 2 (Part A): Enable pgvector and pg_trgm extensions via Azure CLI.
    """
    print("\n" + "=" * 60)
    print("Step 2: Configure PostgreSQL Extensions")
    print("=" * 60)
    
    print("⏳ Enabling extensions (pgvector, uuid-ossp, pg_trgm) on the server...")
    
    # Enable the required extensions
    success, output = run_az_command([
        "postgres", "flexible-server", "parameter", "set",
        "--resource-group", config["resource_group"],
        "--server-name", config["server_name"],
        "--name", "azure.extensions",
        "--value", "vector,uuid-ossp,pg_trgm"
    ])
    
    if success:
        print("✅ Extensions (vector, uuid-ossp, pg_trgm) enabled on server")
        return True
    else:
        print(f"❌ Failed to enable extensions: {output}")
        print("   You may need to enable them manually in Azure Portal:")
        print("   Server → Server parameters → azure.extensions → Add 'vector,uuid-ossp,pg_trgm'")
        return False


def create_database(config: dict, admin_password: str) -> bool:
    """Create the application database."""
    print(f"\n⏳ Creating database '{config['database_name']}'...")
    
    success, output = run_az_command([
        "postgres", "flexible-server", "db", "create",
        "--resource-group", config["resource_group"],
        "--server-name", config["server_name"],
        "--database-name", config["database_name"]
    ])
    
    if success:
        print(f"✅ Database '{config['database_name']}' created")
        return True
    elif "already exists" in output.lower():
        print(f"✅ Database '{config['database_name']}' already exists")
        return True
    else:
        print(f"❌ Failed to create database: {output}")
        return False


async def create_schema(config: dict, admin_password: str) -> bool:
    """
    Step 3: Create schema with pgvector tables.
    """
    print("\n" + "=" * 60)
    print("Step 3: Create Schema")
    print("=" * 60)
    
    try:
        import asyncpg
    except ImportError:
        print("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    
    host = f"{config['server_name']}.postgres.database.azure.com"
    
    print(f"⏳ Connecting to {host}...")
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=5432,
            database=config["database_name"],
            user=config["admin_user"],
            password=admin_password,
            ssl="require"
        )
        
        print("✅ Connected to database")
        
        # Execute schema setup step by step
        print("⏳ Creating extensions...")
        
        # Create extensions
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        
        # Verify pgvector first
        result = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        if not result:
            print("❌ pgvector extension could not be created")
            print("   You may need to enable it in Azure Portal first:")
            print("   Server → Server parameters → azure.extensions → Add 'vector'")
            await conn.close()
            return False
        print(f"✅ pgvector extension version: {result}")
        
        # Create schema
        print(f"⏳ Creating schema '{config['schema_name']}'...")
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {config['schema_name']}")
        
        # Create table
        print("⏳ Creating policy_chunks table...")
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config['schema_name']}.policy_chunks (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                policy_id VARCHAR(50) NOT NULL,
                policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
                policy_name VARCHAR(200) NOT NULL,
                chunk_type VARCHAR(30) NOT NULL,
                chunk_sequence INTEGER NOT NULL DEFAULT 0,
                category VARCHAR(50) NOT NULL,
                subcategory VARCHAR(50),
                criteria_id VARCHAR(50),
                risk_level VARCHAR(30),
                action_recommendation TEXT,
                content TEXT NOT NULL,
                content_hash VARCHAR(64) NOT NULL,
                token_count INTEGER NOT NULL DEFAULT 0,
                embedding VECTOR(1536) NOT NULL,
                embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
                metadata JSONB DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        print("✅ Table created")
        
        # Create indexes
        print("⏳ Creating indexes...")
        
        # HNSW index for vector search
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_embedding 
            ON {config['schema_name']}.policy_chunks 
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)
        
        # Additional indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_category 
            ON {config['schema_name']}.policy_chunks (category)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_policy_id 
            ON {config['schema_name']}.policy_chunks (policy_id)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_risk_level 
            ON {config['schema_name']}.policy_chunks (risk_level)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_chunk_type 
            ON {config['schema_name']}.policy_chunks (chunk_type)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_metadata 
            ON {config['schema_name']}.policy_chunks USING gin (metadata)
        """)
        
        # GIN index for hybrid text search (requires pg_trgm)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_policy_chunks_content_trgm 
            ON {config['schema_name']}.policy_chunks USING gin (content gin_trgm_ops)
        """)
        print("✅ Indexes created")
        
        # Verify extensions
        print("⏳ Verifying extensions...")
        trgm_result = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm'")
        if trgm_result:
            print(f"✅ pg_trgm extension version: {trgm_result}")
        else:
            print("⚠️  pg_trgm extension not found - hybrid search unavailable")
        
        # Verify tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = $1
        """, config["schema_name"])
        
        if tables:
            print(f"✅ Tables in schema '{config['schema_name']}':")
            for table in tables:
                print(f"   - {table['table_name']}")
        
        await conn.close()
        print("\n✅ Schema setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        print("\nTroubleshooting:")
        print("  - Ensure the server is fully provisioned (may take a few minutes)")
        print("  - Check firewall rules allow your IP")
        print("  - Verify the password is correct")
        print("  - Ensure pgvector is enabled: Server → Server parameters → azure.extensions")
        return False


def generate_env_snippet(config: dict, admin_password: str) -> str:
    """Generate .env file snippet for the user."""
    return f"""
# PostgreSQL RAG Configuration (add to .env)
DATABASE_BACKEND=postgresql
POSTGRESQL_HOST={config['server_name']}.postgres.database.azure.com
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE={config['database_name']}
POSTGRESQL_USER={config['admin_user']}
POSTGRESQL_PASSWORD={admin_password}
POSTGRESQL_SSL_MODE=require
POSTGRESQL_SCHEMA={config['schema_name']}

# RAG Configuration
RAG_ENABLED=true
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
"""


def prompt_configuration() -> dict:
    """Prompt user for configuration values."""
    print("\n" + "=" * 60)
    print("Azure PostgreSQL RAG - Configuration")
    print("=" * 60)
    print("\nPress Enter to accept default values.\n")
    
    config = {}
    
    config["resource_group"] = input(
        f"Resource Group [{DEFAULT_CONFIG['resource_group']}]: "
    ).strip() or DEFAULT_CONFIG["resource_group"]
    
    config["server_name"] = input(
        f"Server Name [{DEFAULT_CONFIG['server_name']}]: "
    ).strip() or DEFAULT_CONFIG["server_name"]
    
    config["location"] = input(
        f"Location [{DEFAULT_CONFIG['location']}]: "
    ).strip() or DEFAULT_CONFIG["location"]
    
    config["admin_user"] = input(
        f"Admin Username [{DEFAULT_CONFIG['admin_user']}]: "
    ).strip() or DEFAULT_CONFIG["admin_user"]
    
    config["database_name"] = input(
        f"Database Name [{DEFAULT_CONFIG['database_name']}]: "
    ).strip() or DEFAULT_CONFIG["database_name"]
    
    config["schema_name"] = input(
        f"Schema Name [{DEFAULT_CONFIG['schema_name']}]: "
    ).strip() or DEFAULT_CONFIG["schema_name"]
    
    config["sku_name"] = input(
        f"SKU (compute tier) [{DEFAULT_CONFIG['sku_name']}]: "
    ).strip() or DEFAULT_CONFIG["sku_name"]
    
    config["tier"] = DEFAULT_CONFIG["tier"]
    config["storage_size"] = DEFAULT_CONFIG["storage_size"]
    config["postgres_version"] = DEFAULT_CONFIG["postgres_version"]
    
    return config


def prompt_password() -> str:
    """Prompt for admin password securely."""
    import getpass
    
    while True:
        password = getpass.getpass("Admin Password (min 8 chars, must include uppercase, lowercase, number): ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            continue
        if not any(c.isupper() for c in password):
            print("❌ Password must include at least one uppercase letter")
            continue
        if not any(c.islower() for c in password):
            print("❌ Password must include at least one lowercase letter")
            continue
        if not any(c.isdigit() for c in password):
            print("❌ Password must include at least one number")
            continue
        
        confirm = getpass.getpass("Confirm Password: ")
        if password != confirm:
            print("❌ Passwords do not match")
            continue
        
        return password


def use_existing_connection() -> tuple[bool, dict, str]:
    """Check if PostgreSQL connection is already configured in environment."""
    host = os.getenv("POSTGRESQL_HOST")
    password = os.getenv("POSTGRESQL_PASSWORD")
    
    if host and password:
        print("\n✅ Found existing PostgreSQL configuration in environment:")
        print(f"   Host: {host}")
        print(f"   Database: {os.getenv('POSTGRESQL_DATABASE', 'workbenchiq')}")
        
        response = input("\nUse existing configuration? (Y/n): ").strip().lower()
        if response != 'n':
            config = {
                "server_name": host.replace(".postgres.database.azure.com", ""),
                "database_name": os.getenv("POSTGRESQL_DATABASE", "workbenchiq"),
                "admin_user": os.getenv("POSTGRESQL_USER", "workbenchiq_admin"),
                "schema_name": os.getenv("POSTGRESQL_SCHEMA", "workbenchiq"),
                "resource_group": os.getenv("POSTGRESQL_RESOURCE_GROUP", "workbenchiq-rg"),
                "location": os.getenv("POSTGRESQL_LOCATION", "eastus"),
                "sku_name": DEFAULT_CONFIG["sku_name"],
                "storage_size": DEFAULT_CONFIG["storage_size"],
                "postgres_version": DEFAULT_CONFIG["postgres_version"],
            }
            return True, config, password
    
    return False, {}, ""


async def run_setup():
    """Main setup workflow."""
    print("\n" + "=" * 60)
    print("Azure PostgreSQL RAG Integration - Setup Utility")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Provision Azure PostgreSQL Flexible Server")
    print("  2. Enable pgvector extension")
    print("  3. Create database schema with vector tables")
    
    # Check Azure CLI login
    print("\n" + "-" * 60)
    print("Checking prerequisites...")
    print("-" * 60)
    
    if not check_az_login():
        sys.exit(1)
    
    # Check for existing configuration
    use_existing, config, admin_password = use_existing_connection()
    
    if not use_existing:
        # Get configuration from user
        config = prompt_configuration()
        admin_password = prompt_password()
        
        # Ensure resource group exists
        if not check_resource_group(config["resource_group"]):
            response = input(f"\nResource group '{config['resource_group']}' doesn't exist. Create it? (Y/n): ").strip().lower()
            if response != 'n':
                if not create_resource_group(config["resource_group"], config["location"]):
                    sys.exit(1)
            else:
                print("❌ Cannot proceed without a resource group")
                sys.exit(1)
        else:
            print(f"✅ Resource group '{config['resource_group']}' exists")
        
        # Step 1: Provision PostgreSQL server
        if not provision_postgresql_server(config, admin_password):
            print("\n❌ Setup failed at Step 1")
            sys.exit(1)
        
        # Step 2a: Enable pgvector via Azure CLI
        if not enable_pgvector_extension(config):
            print("\n⚠️  Warning: Could not enable pgvector via CLI")
            print("   Will attempt to enable via SQL connection...")
        
        # Create database
        if not create_database(config, admin_password):
            print("\n❌ Setup failed: Could not create database")
            sys.exit(1)
    
    # Step 2b & 3: Create schema (connects to database)
    print("\n⏳ Waiting for server to be ready...")
    await asyncio.sleep(5)  # Brief wait for server to be fully ready
    
    if not await create_schema(config, admin_password):
        print("\n❌ Setup failed at Step 3")
        sys.exit(1)
    
    # Success - show environment variables
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    
    if not use_existing:
        print("\nAdd the following to your .env file:")
        print("-" * 60)
        print(generate_env_snippet(config, admin_password))
    
    print("\nNext steps:")
    print("  1. Run test_db_connection.py to verify connectivity")
    print("  2. Run test_index_policies.py to index sample policies")
    print("  3. Run test_vector_search.py to test vector search")
    print("\nSee specs/006-azure-postgresql-rag-integration/quickstart.md for details")


def main():
    """Entry point."""
    try:
        asyncio.run(run_setup())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
