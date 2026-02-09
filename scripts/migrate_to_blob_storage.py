#!/usr/bin/env python
"""
Migration script to transfer application and conversation data from local 'data' folder
to Azure Blob Storage.

This script:
1. Checks Azure CLI login status
2. Tests connectivity to Azure Blob Storage
3. Migrates applications to 'applications/' prefix in blob storage
4. Migrates conversations to 'conversations/' prefix in blob storage
5. Provides dry-run mode for testing before actual migration

Usage:
    # Test mode (dry run - no actual uploads)
    uv run python scripts/migrate_to_blob_storage.py --dry-run

    # Actual migration
    uv run python scripts/migrate_to_blob_storage.py --migrate
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from azure.storage.blob import BlobServiceClient, ContainerClient
    from azure.core.exceptions import AzureError
except ImportError:
    print("ERROR: azure-storage-blob package is not installed.")
    print("Install it with: uv pip install azure-storage-blob")
    sys.exit(1)


# Configuration
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "workbenchiq-data")
DATA_ROOT = Path(__file__).parent.parent / "data"


def get_connection_string() -> str:
    """Get Azure Storage connection string from environment variable."""
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        print("❌ AZURE_STORAGE_CONNECTION_STRING environment variable is not set.")
        print("   Set it with: set AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>")
        sys.exit(1)
    return conn_str


class MigrationStats:
    """Track migration statistics."""
    
    def __init__(self):
        self.files_found = 0
        self.files_uploaded = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.bytes_transferred = 0
        self.errors: list[str] = []
    
    def summary(self) -> str:
        return (
            f"\n{'='*60}\n"
            f"Migration Summary\n"
            f"{'='*60}\n"
            f"Files found:      {self.files_found}\n"
            f"Files uploaded:   {self.files_uploaded}\n"
            f"Files skipped:    {self.files_skipped}\n"
            f"Files failed:     {self.files_failed}\n"
            f"Bytes transferred: {self.bytes_transferred:,} ({self.bytes_transferred / (1024*1024):.2f} MB)\n"
            f"{'='*60}"
        )


def check_azure_login() -> bool:
    """Check if user is logged into Azure CLI."""
    print("\n🔐 Checking Azure CLI login status...")
    
    try:
        # Try to find az.cmd on Windows or az on other platforms
        az_cmd = "az.cmd" if sys.platform == "win32" else "az"
        result = subprocess.run(
            [az_cmd, "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True  # Use shell to find az in PATH
        )
        
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            print(f"   ✅ Logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
            print(f"   ✅ Subscription: {account_info.get('name', 'Unknown')}")
            return True
        else:
            print("   ❌ Not logged into Azure CLI")
            print("   Run 'az login' to authenticate")
            return False
            
    except FileNotFoundError:
        print("   ⚠️  Azure CLI not found, but connection string auth will be used")
        return True  # Allow proceeding with connection string auth
    except subprocess.TimeoutExpired:
        print("   ❌ Azure CLI command timed out")
        return False
    except json.JSONDecodeError:
        print("   ⚠️  Could not parse Azure CLI output, but may still be logged in")
        return True


def test_blob_connection(connection_string: str, container_name: str) -> Optional[ContainerClient]:
    """Test connection to Azure Blob Storage and ensure container exists."""
    print("\n🔗 Testing Azure Blob Storage connection...")
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get account info
        account_info = blob_service_client.get_account_information()
        print(f"   ✅ Connected to storage account")
        print(f"   ✅ SKU: {account_info.get('sku_name', 'Unknown')}")
        
        # Get or create container
        container_client = blob_service_client.get_container_client(container_name)
        
        if not container_client.exists():
            print(f"   📦 Container '{container_name}' does not exist. Creating...")
            container_client.create_container()
            print(f"   ✅ Container '{container_name}' created")
        else:
            print(f"   ✅ Container '{container_name}' exists")
        
        return container_client
        
    except AzureError as e:
        print(f"   ❌ Azure error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return None


def collect_files(data_root: Path) -> list[tuple[Path, str]]:
    """
    Collect all files to migrate with their blob paths.
    
    Returns list of tuples: (local_path, blob_path)
    """
    files_to_migrate = []
    
    # Migrate applications
    applications_dir = data_root / "applications"
    if applications_dir.exists():
        for file_path in applications_dir.rglob("*"):
            if file_path.is_file() and file_path.name != ".gitkeep":
                # Construct blob path: applications/{app_id}/...
                relative_path = file_path.relative_to(data_root)
                blob_path = str(relative_path).replace("\\", "/")
                files_to_migrate.append((file_path, blob_path))
    
    # Migrate conversations
    conversations_dir = data_root / "conversations"
    if conversations_dir.exists():
        for file_path in conversations_dir.rglob("*"):
            if file_path.is_file() and file_path.name != ".gitkeep":
                # Construct blob path: conversations/{app_id}/...
                relative_path = file_path.relative_to(data_root)
                blob_path = str(relative_path).replace("\\", "/")
                files_to_migrate.append((file_path, blob_path))
    
    return files_to_migrate


def dry_run(data_root: Path) -> MigrationStats:
    """Perform a dry run - list all files that would be migrated."""
    print("\n🧪 DRY RUN MODE - No files will be uploaded")
    print("="*60)
    
    stats = MigrationStats()
    files_to_migrate = collect_files(data_root)
    
    print(f"\n📁 Source directory: {data_root}")
    print(f"📦 Target container: {CONTAINER_NAME}")
    print(f"\nFiles to be migrated:\n")
    
    current_prefix = ""
    for local_path, blob_path in files_to_migrate:
        stats.files_found += 1
        file_size = local_path.stat().st_size
        stats.bytes_transferred += file_size
        
        # Print section headers
        prefix = blob_path.split("/")[0]
        if prefix != current_prefix:
            current_prefix = prefix
            print(f"\n  [{prefix.upper()}]")
        
        # Print file info
        size_str = f"{file_size:,} bytes" if file_size < 1024 else f"{file_size/1024:.1f} KB"
        print(f"    📄 {blob_path} ({size_str})")
    
    if stats.files_found == 0:
        print("  (No files found to migrate)")
    
    print(stats.summary())
    print("\n✅ Dry run complete. Run with --migrate to perform actual migration.")
    
    return stats


def migrate(container_client: ContainerClient, data_root: Path, skip_existing: bool = True) -> MigrationStats:
    """Perform the actual migration to Azure Blob Storage."""
    print("\n🚀 MIGRATION MODE - Uploading files to Azure Blob Storage")
    print("="*60)
    
    stats = MigrationStats()
    files_to_migrate = collect_files(data_root)
    
    print(f"\n📁 Source directory: {data_root}")
    print(f"📦 Target container: {CONTAINER_NAME}")
    print(f"📊 Total files to process: {len(files_to_migrate)}")
    print()
    
    for i, (local_path, blob_path) in enumerate(files_to_migrate, 1):
        stats.files_found += 1
        file_size = local_path.stat().st_size
        
        try:
            blob_client = container_client.get_blob_client(blob_path)
            
            # Check if blob already exists
            if skip_existing and blob_client.exists():
                print(f"  [{i}/{len(files_to_migrate)}] ⏭️  Skipped (exists): {blob_path}")
                stats.files_skipped += 1
                continue
            
            # Upload the file
            with open(local_path, "rb") as file_data:
                blob_client.upload_blob(file_data, overwrite=True)
            
            stats.files_uploaded += 1
            stats.bytes_transferred += file_size
            size_str = f"{file_size:,} bytes" if file_size < 1024 else f"{file_size/1024:.1f} KB"
            print(f"  [{i}/{len(files_to_migrate)}] ✅ Uploaded: {blob_path} ({size_str})")
            
        except AzureError as e:
            stats.files_failed += 1
            error_msg = f"Failed to upload {blob_path}: {e}"
            stats.errors.append(error_msg)
            print(f"  [{i}/{len(files_to_migrate)}] ❌ Failed: {blob_path} - {e}")
        except Exception as e:
            stats.files_failed += 1
            error_msg = f"Error uploading {blob_path}: {e}"
            stats.errors.append(error_msg)
            print(f"  [{i}/{len(files_to_migrate)}] ❌ Error: {blob_path} - {e}")
    
    print(stats.summary())
    
    if stats.errors:
        print("\n⚠️  Errors encountered:")
        for error in stats.errors[:10]:  # Show first 10 errors
            print(f"    - {error}")
        if len(stats.errors) > 10:
            print(f"    ... and {len(stats.errors) - 10} more errors")
    
    if stats.files_failed == 0:
        print("\n✅ Migration completed successfully!")
    else:
        print(f"\n⚠️  Migration completed with {stats.files_failed} failures")
    
    return stats


def verify_migration(container_client: ContainerClient) -> None:
    """Verify the migration by listing blobs in the container."""
    print("\n🔍 Verifying migration - listing blobs in container...")
    
    applications_count = 0
    conversations_count = 0
    
    for blob in container_client.list_blobs():
        if blob.name.startswith("applications/"):
            applications_count += 1
        elif blob.name.startswith("conversations/"):
            conversations_count += 1
    
    print(f"   📁 Applications blobs: {applications_count}")
    print(f"   💬 Conversations blobs: {conversations_count}")
    print(f"   📊 Total blobs: {applications_count + conversations_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate local data to Azure Blob Storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test what would be migrated (no uploads)
    python scripts/migrate_to_blob_storage.py --dry-run

    # Perform actual migration
    python scripts/migrate_to_blob_storage.py --migrate

    # Force overwrite existing blobs
    python scripts/migrate_to_blob_storage.py --migrate --overwrite

    # Verify migration after completion
    python scripts/migrate_to_blob_storage.py --verify
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be migrated without uploading"
    )
    group.add_argument(
        "--migrate",
        action="store_true",
        help="Perform the actual migration"
    )
    group.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration by listing blobs in container"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing blobs (default: skip existing)"
    )
    parser.add_argument(
        "--skip-azure-check",
        action="store_true",
        help="Skip Azure CLI login check"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  Azure Blob Storage Migration Tool")
    print("="*60)
    
    # Check data directory exists
    if not DATA_ROOT.exists():
        print(f"\n❌ Data directory not found: {DATA_ROOT}")
        sys.exit(1)
    
    print(f"\n📁 Data directory: {DATA_ROOT}")
    
    # Check Azure login (unless skipped or dry-run)
    if not args.skip_azure_check and not args.dry_run:
        if not check_azure_login():
            print("\n❌ Please login to Azure CLI first: az login")
            sys.exit(1)
    
    # For dry-run, we don't need blob connection
    if args.dry_run:
        dry_run(DATA_ROOT)
        return
    
    # Test blob connection
    connection_string = get_connection_string()
    container_client = test_blob_connection(connection_string, CONTAINER_NAME)
    if not container_client:
        print("\n❌ Failed to connect to Azure Blob Storage")
        sys.exit(1)
    
    if args.verify:
        verify_migration(container_client)
        return
    
    if args.migrate:
        # Confirm before migration
        print("\n⚠️  This will upload files to Azure Blob Storage.")
        response = input("Continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("Migration cancelled.")
            sys.exit(0)
        
        stats = migrate(container_client, DATA_ROOT, skip_existing=not args.overwrite)
        
        # Verify after migration
        verify_migration(container_client)


if __name__ == "__main__":
    main()
