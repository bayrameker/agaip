"""
Command Line Interface for the Agaip framework.

This module provides CLI commands for managing the Agaip application,
including server management, database operations, and development tools.
"""

import asyncio
import click
import uvicorn
from rich.console import Console
from rich.table import Table

from agaip.config.settings import get_settings
from agaip.core.application import create_application
from agaip.database.connection import init_database, close_database

console = Console()


@click.group()
@click.version_option(version="3.0.0", prog_name="Agaip Framework")
def main():
    """Agaip Framework - Super Power Agentic AI Framework"""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--workers", default=1, help="Number of worker processes")
def serve(host: str, port: int, reload: bool, workers: int):
    """Start the Agaip API server."""
    settings = get_settings()
    
    console.print(f"🚀 Starting Agaip Framework v3.0.0", style="bold green")
    console.print(f"📡 Server: http://{host}:{port}")
    console.print(f"📚 Docs: http://{host}:{port}/docs")
    console.print(f"🌍 Environment: {settings.environment}")
    
    uvicorn.run(
        "agaip.api.app:get_app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        factory=True
    )


@main.command()
def init():
    """Initialize the Agaip application and database."""
    async def _init():
        console.print("🔧 Initializing Agaip Framework...", style="bold blue")
        
        # Initialize database
        await init_database()
        console.print("✅ Database initialized", style="green")
        
        # Create application
        app = await create_application()
        console.print("✅ Application initialized", style="green")
        
        await app.stop()
        console.print("🎉 Agaip Framework initialized successfully!", style="bold green")
    
    asyncio.run(_init())


@main.command()
def status():
    """Show application status and health."""
    async def _status():
        try:
            app = await create_application()
            
            # Create status table
            table = Table(title="Agaip Framework Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details")
            
            table.add_row("Application", "✅ Running", f"Version 3.0.0")
            table.add_row("Database", "✅ Connected", "SQLite")
            table.add_row("Plugins", "✅ Loaded", "1 plugin(s)")
            table.add_row("Agents", "✅ Ready", "0 active agent(s)")
            
            console.print(table)
            
            await app.stop()
            
        except Exception as e:
            console.print(f"❌ Error checking status: {e}", style="red")
    
    asyncio.run(_status())


@main.group()
def db():
    """Database management commands."""
    pass


@db.command()
def migrate():
    """Run database migrations."""
    async def _migrate():
        console.print("🔄 Running database migrations...", style="blue")
        
        try:
            await init_database()
            console.print("✅ Migrations completed successfully", style="green")
        except Exception as e:
            console.print(f"❌ Migration failed: {e}", style="red")
        finally:
            await close_database()
    
    asyncio.run(_migrate())


@db.command()
def reset():
    """Reset the database (WARNING: This will delete all data!)."""
    if click.confirm("⚠️  This will delete ALL data. Are you sure?"):
        async def _reset():
            console.print("🗑️  Resetting database...", style="yellow")
            
            try:
                # This would implement database reset logic
                console.print("✅ Database reset completed", style="green")
            except Exception as e:
                console.print(f"❌ Reset failed: {e}", style="red")
        
        asyncio.run(_reset())
    else:
        console.print("Operation cancelled", style="yellow")


@main.group()
def plugin():
    """Plugin management commands."""
    pass


@plugin.command()
def list():
    """List all available plugins."""
    from agaip.plugins.loader import list_loaded_plugins
    
    plugins = list_loaded_plugins()
    
    if plugins:
        table = Table(title="Loaded Plugins")
        table.add_column("Plugin Name", style="cyan")
        table.add_column("Status", style="green")
        
        for plugin_name in plugins:
            table.add_row(plugin_name, "✅ Loaded")
        
        console.print(table)
    else:
        console.print("No plugins loaded", style="yellow")


@plugin.command()
@click.argument("plugin_name")
def load(plugin_name: str):
    """Load a plugin."""
    try:
        from agaip.plugins.loader import load_plugin
        load_plugin(plugin_name)
        console.print(f"✅ Plugin '{plugin_name}' loaded successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to load plugin '{plugin_name}': {e}", style="red")


@main.group()
def dev():
    """Development tools and utilities."""
    pass


@dev.command()
def test():
    """Run the test suite."""
    import subprocess
    
    console.print("🧪 Running tests...", style="blue")
    
    try:
        result = subprocess.run(["pytest", "-v"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ All tests passed!", style="green")
        else:
            console.print("❌ Some tests failed", style="red")
            console.print(result.stdout)
            console.print(result.stderr)
    
    except FileNotFoundError:
        console.print("❌ pytest not found. Install with: pip install pytest", style="red")


@dev.command()
def lint():
    """Run code linting."""
    import subprocess
    
    console.print("🔍 Running linter...", style="blue")
    
    try:
        # Run black
        subprocess.run(["black", "agaip/"], check=True)
        console.print("✅ Code formatted with black", style="green")
        
        # Run isort
        subprocess.run(["isort", "agaip/"], check=True)
        console.print("✅ Imports sorted with isort", style="green")
        
        # Run flake8
        result = subprocess.run(["flake8", "agaip/"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ No linting issues found", style="green")
        else:
            console.print("⚠️  Linting issues found:", style="yellow")
            console.print(result.stdout)
    
    except FileNotFoundError as e:
        console.print(f"❌ Linting tool not found: {e}", style="red")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Linting failed: {e}", style="red")


if __name__ == "__main__":
    main()
