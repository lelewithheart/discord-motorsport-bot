"""Universal paginator view for multi-page embeds."""

from __future__ import annotations

from typing import List, Optional

import discord


class Paginator(discord.ui.View):
    """A universal paginator with first / prev / stop / next / last buttons.

    Parameters
    ----------
    pages : list[discord.Embed]
        The embeds to paginate through.
    user_id : int, optional
        If set, only this user may interact with the buttons.
    timeout : float
        Seconds before the view times out (default: 180).
    """

    def __init__(
        self,
        pages: List[discord.Embed],
        user_id: Optional[int] = None,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current = 0
        self.user_id = user_id

        # Build buttons manually so we control custom_id values
        self.first_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary, emoji="⏮", custom_id="paginator_first"
        )
        self.first_btn.callback = self._first_page

        self.prev_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary, emoji="◀️", custom_id="paginator_prev"
        )
        self.prev_btn.callback = self._prev_page

        self.stop_btn = discord.ui.Button(
            style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="paginator_stop"
        )
        self.stop_btn.callback = self._stop_view

        self.next_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary, emoji="▶️", custom_id="paginator_next"
        )
        self.next_btn.callback = self._next_page

        self.last_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary, emoji="⏭", custom_id="paginator_last"
        )
        self.last_btn.callback = self._last_page

        # Map for quick access in _update_buttons
        self._buttons = {
            "first": self.first_btn,
            "prev": self.prev_btn,
            "stop": self.stop_btn,
            "next": self.next_btn,
            "last": self.last_btn,
        }

        for btn in self._buttons.values():
            self.add_item(btn)

        self._update_buttons()

    # ── Button callbacks ─────────────────────────────────────────────────

    async def _first_page(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.current = 0
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current], view=self
        )

    async def _prev_page(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.current = max(0, self.current - 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current], view=self
        )

    async def _stop_view(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def _next_page(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.current = min(len(self.pages) - 1, self.current + 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current], view=self
        )

    async def _last_page(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.current = len(self.pages) - 1
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current], view=self
        )

    # ── Internal helpers ──────────────────────────────────────────────────

    def _check_user(self, interaction: discord.Interaction) -> bool:
        """Return True if the user is not allowed to interact."""
        return self.user_id is not None and interaction.user.id != self.user_id

    def _update_buttons(self) -> None:
        """Enable/disable navigation buttons based on current page index."""
        if len(self.pages) <= 1:
            for btn in self._buttons.values():
                btn.disabled = True
            return

        self._buttons["first"].disabled = self.current == 0
        self._buttons["prev"].disabled = self.current == 0
        self._buttons["next"].disabled = self.current == len(self.pages) - 1
        self._buttons["last"].disabled = self.current == len(self.pages) - 1
        # stop is always enabled

    async def on_timeout(self) -> None:
        """Clean up on timeout."""
        self.stop()
