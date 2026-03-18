"""Cache management commands."""

from __future__ import annotations

from typing import Annotated

import typer

from mixy.infrastructure.cache import CacheStore


def create_cache_app(cache_store: CacheStore | None = None) -> typer.Typer:
    app = typer.Typer(help="Manage cached Git sources.")

    def get_store() -> CacheStore:
        if cache_store is not None:
            return cache_store
        return CacheStore()

    @app.command("list")
    def list_cache() -> None:
        store = get_store()
        entries = store.list_entries()
        if not entries:
            typer.echo("Cache is empty.")
            return

        typer.echo("URL | REF | SHA | SIZE")
        for entry in entries:
            typer.echo(f"{entry.url} | {entry.ref} | {entry.sha} | {entry.size}")

    @app.command("clear")
    def clear_cache(
        url: Annotated[
            str | None,
            typer.Option("--url", help="Clear cache entries for a specific repository URL."),
        ] = None,
    ) -> None:
        store = get_store()
        if url is None:
            store.clear_all()
            typer.echo("Cleared all cache entries.")
            return

        store.clear_by_url(url)
        typer.echo(f"Cleared cache entries for {url}.")

    return app
