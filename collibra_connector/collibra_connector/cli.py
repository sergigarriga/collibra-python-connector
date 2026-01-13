"""
Command-Line Interface for Collibra Connector.

This module provides a CLI tool for interacting with Collibra
directly from the terminal without writing code.

Installation:
    pip install collibra-connector[cli]

Usage:
    collibra-sdk --help
    collibra-sdk search "Business Term" --format json
    collibra-sdk export-domain --id "uuid" --output report.csv
    collibra-sdk get-asset --id "uuid"
"""
from __future__ import annotations

import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

if CLICK_AVAILABLE:
    from click import Context, echo, style, secho


def get_connector():
    """Create connector from environment variables."""
    from .connector import CollibraConnector

    api = os.environ.get("COLLIBRA_URL")
    username = os.environ.get("COLLIBRA_USERNAME")
    password = os.environ.get("COLLIBRA_PASSWORD")

    if not all([api, username, password]):
        raise click.ClickException(
            "Missing environment variables. Set:\n"
            "  COLLIBRA_URL=https://your-instance.collibra.com\n"
            "  COLLIBRA_USERNAME=your-username\n"
            "  COLLIBRA_PASSWORD=your-password"
        )

    return CollibraConnector(api=api, username=username, password=password)


def format_output(data: Any, fmt: str) -> str:
    """Format output data based on format type."""
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)
    elif fmt == "table":
        if isinstance(data, list) and data:
            # Simple table format
            headers = list(data[0].keys())
            lines = ["\t".join(headers)]
            for item in data:
                lines.append("\t".join(str(item.get(h, "")) for h in headers))
            return "\n".join(lines)
        return str(data)
    elif fmt == "csv":
        if isinstance(data, list) and data:
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        return str(data)
    else:
        return str(data)


if CLICK_AVAILABLE:
    @click.group()
    @click.version_option(version="1.2.0", prog_name="collibra-sdk")
    @click.pass_context
    def cli(ctx: Context) -> None:
        """
        Collibra SDK - Command line interface for Collibra Data Governance.

        Configure connection using environment variables:

          export COLLIBRA_URL=https://your-instance.collibra.com

          export COLLIBRA_USERNAME=your-username

          export COLLIBRA_PASSWORD=your-password
        """
        ctx.ensure_object(dict)

    # ==========================================================================
    # Connection Commands
    # ==========================================================================

    @cli.command("test")
    def test_connection() -> None:
        """Test the connection to Collibra."""
        try:
            conn = get_connector()
            if conn.test_connection():
                secho("Connection successful!", fg="green")
            else:
                secho("Connection failed.", fg="red")
                sys.exit(1)
        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    @cli.command("info")
    def show_info() -> None:
        """Show connection and version information."""
        try:
            conn = get_connector()
            echo(f"Collibra URL: {conn.base_url}")
            echo(f"SDK Version: {conn.get_version()}")

            if conn.test_connection():
                secho("Status: Connected", fg="green")
            else:
                secho("Status: Not Connected", fg="red")
        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Search Commands
    # ==========================================================================

    @cli.command("search")
    @click.argument("query")
    @click.option("--type", "-t", "asset_type", help="Filter by asset type name")
    @click.option("--domain", "-d", "domain_id", help="Filter by domain ID")
    @click.option("--community", "-c", "community_id", help="Filter by community ID")
    @click.option("--limit", "-l", default=10, help="Maximum results (default: 10)")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]),
                  help="Output format")
    def search_assets(
        query: str,
        asset_type: Optional[str],
        domain_id: Optional[str],
        community_id: Optional[str],
        limit: int,
        fmt: str
    ) -> None:
        """
        Search for assets in Collibra.

        Examples:

          collibra-sdk search "Customer"

          collibra-sdk search "Product*" --limit 50 --format json

          collibra-sdk search "Order" --type "Business Term"
        """
        try:
            conn = get_connector()

            # Prepare filters
            type_ids = None
            if asset_type:
                # Look up type ID by name
                types = conn.metadata.get_asset_types(name=asset_type, limit=1)
                if types.get("results"):
                    type_ids = [types["results"][0]["id"]]
                else:
                    secho(f"Asset type not found: {asset_type}", fg="yellow")

            domain_ids = [domain_id] if domain_id else None
            community_ids = [community_id] if community_id else None

            # Execute search
            result = conn.search.find_assets(
                query=query,
                limit=limit,
                type_ids=type_ids,
                domain_ids=domain_ids,
                community_ids=community_ids
            )

            # Format results
            items = []
            for item in result.get("results", []):
                resource = item.get("resource", {})
                items.append({
                    "id": resource.get("id"),
                    "name": resource.get("name") or resource.get("displayName"),
                    "type": resource.get("resourceType"),
                    "score": item.get("score", 0)
                })

            if not items:
                echo("No results found.")
                return

            echo(f"Found {result.get('total', 0)} results (showing {len(items)}):\n")
            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Asset Commands
    # ==========================================================================

    @cli.command("get-asset")
    @click.option("--id", "asset_id", required=True, help="Asset UUID")
    @click.option("--format", "-f", "fmt", default="json",
                  type=click.Choice(["json", "table"]),
                  help="Output format")
    @click.option("--full", is_flag=True, help="Include attributes and relations")
    def get_asset(asset_id: str, fmt: str, full: bool) -> None:
        """
        Get details for a specific asset.

        Examples:

          collibra-sdk get-asset --id "abc-123-uuid"

          collibra-sdk get-asset --id "abc-123-uuid" --full
        """
        try:
            conn = get_connector()

            if full:
                result = conn.asset.get_full_profile(asset_id)
                # Flatten for display
                output = {
                    "id": result["asset"].get("id"),
                    "name": result["asset"].get("name"),
                    "display_name": result["asset"].get("displayName"),
                    "type": result["asset"].get("type", {}).get("name"),
                    "status": result["asset"].get("status", {}).get("name"),
                    "domain": result["asset"].get("domain", {}).get("name"),
                    "attributes": result.get("attributes", {}),
                    "relations_outgoing": result["relations"].get("outgoing_count", 0),
                    "relations_incoming": result["relations"].get("incoming_count", 0),
                    "responsibilities": result.get("responsibilities", [])
                }
            else:
                output = conn.asset.get_asset(asset_id)

            echo(format_output(output, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    @cli.command("list-assets")
    @click.option("--domain", "-d", "domain_id", help="Filter by domain ID")
    @click.option("--community", "-c", "community_id", help="Filter by community ID")
    @click.option("--type", "-t", "type_ids", multiple=True, help="Filter by type ID(s)")
    @click.option("--limit", "-l", default=100, help="Maximum results")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]),
                  help="Output format")
    def list_assets(
        domain_id: Optional[str],
        community_id: Optional[str],
        type_ids: tuple,
        limit: int,
        fmt: str
    ) -> None:
        """
        List assets with optional filters.

        Examples:

          collibra-sdk list-assets --domain "uuid"

          collibra-sdk list-assets --limit 50 --format csv > assets.csv
        """
        try:
            conn = get_connector()

            result = conn.asset.find_assets(
                domain_id=domain_id,
                community_id=community_id,
                asset_type_ids=list(type_ids) if type_ids else None,
                limit=limit
            )

            items = []
            for asset in result.get("results", []):
                items.append({
                    "id": asset.get("id"),
                    "name": asset.get("name"),
                    "type": asset.get("type", {}).get("name"),
                    "status": asset.get("status", {}).get("name"),
                    "domain": asset.get("domain", {}).get("name")
                })

            echo(f"Total: {result.get('total', 0)} assets\n")
            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Export Commands
    # ==========================================================================

    @cli.command("export-domain")
    @click.option("--id", "domain_id", required=True, help="Domain UUID")
    @click.option("--output", "-o", "output_file", required=True,
                  help="Output file path (.csv or .json)")
    @click.option("--include-attributes", is_flag=True, default=True,
                  help="Include asset attributes")
    @click.option("--include-relations", is_flag=True, default=False,
                  help="Include relation summaries")
    @click.option("--limit", "-l", default=1000, help="Maximum assets to export")
    def export_domain(
        domain_id: str,
        output_file: str,
        include_attributes: bool,
        include_relations: bool,
        limit: int
    ) -> None:
        """
        Export all assets in a domain to a file.

        Examples:

          collibra-sdk export-domain --id "uuid" --output assets.csv

          collibra-sdk export-domain --id "uuid" --output data.json --include-relations
        """
        try:
            from .helpers import DataFrameExporter

            conn = get_connector()
            exporter = DataFrameExporter(conn)

            echo(f"Exporting domain {domain_id}...")

            df = exporter.assets_to_dataframe(
                domain_id=domain_id,
                limit=limit,
                include_attributes=include_attributes,
                include_relations=include_relations
            )

            if output_file.endswith(".csv"):
                df.to_csv(output_file, index=False)
            elif output_file.endswith(".json"):
                df.to_json(output_file, orient="records", indent=2)
            elif output_file.endswith(".xlsx"):
                df.to_excel(output_file, index=False)
            else:
                df.to_csv(output_file, index=False)

            secho(f"Exported {len(df)} assets to {output_file}", fg="green")

        except ImportError:
            secho("Pandas is required for export. Install with: pip install pandas", fg="red")
            sys.exit(1)
        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    @cli.command("export-community")
    @click.option("--id", "community_id", required=True, help="Community UUID")
    @click.option("--output", "-o", "output_file", required=True,
                  help="Output file path")
    @click.option("--include-attributes", is_flag=True, default=True)
    @click.option("--limit", "-l", default=1000)
    def export_community(
        community_id: str,
        output_file: str,
        include_attributes: bool,
        limit: int
    ) -> None:
        """
        Export all assets in a community to a file.

        Examples:

          collibra-sdk export-community --id "uuid" --output assets.csv
        """
        try:
            from .helpers import DataFrameExporter

            conn = get_connector()
            exporter = DataFrameExporter(conn)

            echo(f"Exporting community {community_id}...")

            df = exporter.assets_to_dataframe(
                community_id=community_id,
                limit=limit,
                include_attributes=include_attributes
            )

            if output_file.endswith(".csv"):
                df.to_csv(output_file, index=False)
            elif output_file.endswith(".json"):
                df.to_json(output_file, orient="records", indent=2)
            else:
                df.to_csv(output_file, index=False)

            secho(f"Exported {len(df)} assets to {output_file}", fg="green")

        except ImportError:
            secho("Pandas required. Install with: pip install pandas", fg="red")
            sys.exit(1)
        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Community/Domain Commands
    # ==========================================================================

    @cli.command("list-communities")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]))
    @click.option("--limit", "-l", default=100)
    def list_communities(fmt: str, limit: int) -> None:
        """List all communities."""
        try:
            conn = get_connector()
            result = conn.community.find_communities(limit=limit)

            items = []
            for comm in result.get("results", []):
                items.append({
                    "id": comm.get("id"),
                    "name": comm.get("name"),
                    "description": (comm.get("description") or "")[:50],
                    "parent": comm.get("parent", {}).get("name") if comm.get("parent") else None
                })

            echo(f"Total: {result.get('total', 0)} communities\n")
            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    @cli.command("list-domains")
    @click.option("--community", "-c", "community_id", help="Filter by community ID")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]))
    @click.option("--limit", "-l", default=100)
    def list_domains(community_id: Optional[str], fmt: str, limit: int) -> None:
        """List all domains."""
        try:
            conn = get_connector()
            result = conn.domain.find_domains(community_id=community_id, limit=limit)

            items = []
            for domain in result.get("results", []):
                items.append({
                    "id": domain.get("id"),
                    "name": domain.get("name"),
                    "type": domain.get("type", {}).get("name"),
                    "community": domain.get("community", {}).get("name")
                })

            echo(f"Total: {result.get('total', 0)} domains\n")
            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Metadata Commands
    # ==========================================================================

    @cli.command("list-asset-types")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]))
    @click.option("--limit", "-l", default=100)
    def list_asset_types(fmt: str, limit: int) -> None:
        """List all asset types."""
        try:
            conn = get_connector()
            result = conn.metadata.get_asset_types()

            items = []
            for at in result.get("results", [])[:limit]:  # Apply limit manually
                items.append({
                    "id": at.get("id"),
                    "name": at.get("name"),
                    "public_id": at.get("publicId"),
                    "description": (at.get("description") or "")[:40]
                })

            echo(f"Total: {result.get('total', 0)} asset types (showing {len(items)})\n")
            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    @cli.command("list-statuses")
    @click.option("--format", "-f", "fmt", default="table",
                  type=click.Choice(["json", "table", "csv"]))
    def list_statuses(fmt: str) -> None:
        """List all statuses."""
        try:
            conn = get_connector()
            result = conn.metadata.get_statuses()

            items = []
            for status in result.get("results", []):
                items.append({
                    "id": status.get("id"),
                    "name": status.get("name"),
                    "description": (status.get("description") or "")[:40]
                })

            echo(format_output(items, fmt))

        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)

    # ==========================================================================
    # Bulk Operations
    # ==========================================================================

    @cli.command("bulk-update-status")
    @click.option("--input", "-i", "input_file", required=True,
                  help="CSV file with 'id' column")
    @click.option("--status-id", required=True, help="New status UUID")
    @click.option("--dry-run", is_flag=True, help="Preview without making changes")
    def bulk_update_status(input_file: str, status_id: str, dry_run: bool) -> None:
        """
        Update status for multiple assets from a CSV file.

        The input file should have an 'id' column with asset UUIDs.

        Examples:

          collibra-sdk bulk-update-status --input assets.csv --status-id "uuid"

          collibra-sdk bulk-update-status --input assets.csv --status-id "uuid" --dry-run
        """
        try:
            import pandas as pd

            conn = get_connector()
            df = pd.read_csv(input_file)

            if "id" not in df.columns:
                secho("Error: CSV must have an 'id' column", fg="red")
                sys.exit(1)

            asset_ids = df["id"].tolist()
            echo(f"Found {len(asset_ids)} assets to update")

            if dry_run:
                echo("Dry run - no changes made")
                return

            success = 0
            errors = 0

            with click.progressbar(asset_ids, label="Updating assets") as bar:
                for asset_id in bar:
                    try:
                        conn.asset.change_asset(asset_id=asset_id, status_id=status_id)
                        success += 1
                    except Exception:
                        errors += 1

            secho(f"Updated: {success}, Errors: {errors}", fg="green" if errors == 0 else "yellow")

        except ImportError:
            secho("Pandas required. Install with: pip install pandas", fg="red")
            sys.exit(1)
        except Exception as e:
            secho(f"Error: {e}", fg="red")
            sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    if not CLICK_AVAILABLE:
        print("CLI requires 'click' package. Install with: pip install click")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
