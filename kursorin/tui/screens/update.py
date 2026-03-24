"""
KURSORIN TUI — Update Screen

Git-based update management view.
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Button, Rule

from kursorin import __version__


class UpdateScreen(Container):
    """Update management view."""

    DEFAULT_CSS = """
    UpdateScreen {
        height: 100%;
    }
    #update-log {
        height: 1fr;
        background: #070a14;
        border: round #1e3a5f;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #3b82f6]🔄 Updates[/]  [#64748b]Keep KURSORIN up to date[/]",
            classes="section-title"
        )
        yield Rule()

        yield Static(
            f"[bold #e2e8f0]Current Version:[/] [#3b82f6]v{__version__}[/]",
            id="current-version"
        )
        yield Static("")

        yield Button(
            "🔍  Check for Updates",
            id="btn-check-update",
            classes="action-btn -primary"
        )
        yield Button(
            "⬇  Pull Update",
            id="btn-pull-update",
            classes="action-btn"
        )
        yield Button(
            "⚠  Force Update (overwrite local)",
            id="btn-force-update",
            classes="action-btn -danger"
        )

        yield Static("")
        yield Static("[bold #3b82f6]📋 Update Log[/]", classes="section-title")
        yield Rule()
        yield VerticalScroll(id="update-log")

    async def check_updates(self) -> None:
        """Check for available updates."""
        log = self.query_one("#update-log", VerticalScroll)
        await log.mount(Static("[#64748b]Checking for updates...[/]"))

        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()

            if not updater.check_git_installed():
                await log.mount(Static("[#ef4444]✖ Git not found. Please install Git.[/]"))
                return

            if not updater.is_git_repo():
                await log.mount(Static("[#f59e0b]⚠ Not a Git repository. Attempting auto-conversion...[/]"))
                success, git_msg = updater.auto_convert_to_git()
                if not success:
                    await log.mount(Static(f"[#ef4444]✖ Auto-conversion failed: {git_msg}[/]"))
                    return
                await log.mount(Static("[#22c55e]✓ Successfully tracked Git repository![/]"))

            available, msg = updater.check_for_updates()
            if available:
                await log.mount(Static("[#22c55e]✓ Update available![/]"))
            else:
                await log.mount(Static(f"[#22c55e]✓ {msg}[/]"))
        except Exception as e:
            await log.mount(Static(f"[#ef4444]✖ Error: {e}[/]"))

    async def pull_update(self, force: bool = False) -> None:
        """Pull the latest update."""
        log = self.query_one("#update-log", VerticalScroll)
        mode = "force" if force else "normal"
        await log.mount(Static(f"[#64748b]Pulling update ({mode})...[/]"))

        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            success, msg = updater.pull_update(force=force)

            if success:
                await log.mount(
                    Static(f"[#22c55e]✓ {msg}[/]\n"
                           "[bold #22c55e]Please restart KURSORIN to apply changes.[/]")
                )
            else:
                await log.mount(Static(f"[#ef4444]✖ {msg}[/]"))
        except Exception as e:
            await log.mount(Static(f"[#ef4444]✖ Error: {e}[/]"))
