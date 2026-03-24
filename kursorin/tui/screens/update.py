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
        background: #050a12;
        border: round #0d2137;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #06d6a0]🔄 Updates[/]  [#576574]Keep KURSORIN up to date[/]",
            classes="section-title"
        )
        yield Rule()

        yield Static(
            f"[bold #c8d6e5]Current Version:[/] [#06d6a0]v{__version__}[/]",
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
        yield Static("[bold #06d6a0]📋 Update Log[/]", classes="section-title")
        yield Rule()
        yield VerticalScroll(id="update-log")

    async def check_updates(self) -> None:
        """Check for available updates."""
        log = self.query_one("#update-log", VerticalScroll)
        await log.mount(Static("[#576574]Checking for updates...[/]"))

        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()

            if not updater.check_git_installed():
                await log.mount(Static("[#ee5a6f]✖ Git not found. Please install Git.[/]"))
                return

            if not updater.is_git_repo():
                await log.mount(Static("[#e1b12c]⚠ Not a Git repository. Attempting auto-conversion to Git...[/]"))
                success, git_msg = updater.auto_convert_to_git()
                if not success:
                    await log.mount(Static(f"[#ee5a6f]✖ Auto-conversion failed: {git_msg}[/]"))
                    return
                await log.mount(Static("[#06d6a0]✓ Successfully tracked Git repository![/]"))

            available, msg = updater.check_for_updates()
            if available:
                await log.mount(Static("[#06d6a0]✓ Update available![/]"))
            else:
                await log.mount(Static(f"[#06d6a0]✓ {msg}[/]"))
        except Exception as e:
            await log.mount(Static(f"[#ee5a6f]✖ Error: {e}[/]"))

    async def pull_update(self, force: bool = False) -> None:
        """Pull the latest update."""
        log = self.query_one("#update-log", VerticalScroll)
        mode = "force" if force else "normal"
        await log.mount(Static(f"[#576574]Pulling update ({mode})...[/]"))

        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            success, msg = updater.pull_update(force=force)

            if success:
                await log.mount(
                    Static(f"[#06d6a0]✓ {msg}[/]\n"
                           "[bold #06d6a0]Please restart KURSORIN to apply changes.[/]")
                )
            else:
                await log.mount(Static(f"[#ee5a6f]✖ {msg}[/]"))
        except Exception as e:
            await log.mount(Static(f"[#ee5a6f]✖ Error: {e}[/]"))
