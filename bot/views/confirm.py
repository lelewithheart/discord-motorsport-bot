"""Confirmation and choice UI views."""

from __future__ import annotations

from typing import Awaitable, Callable, List, Optional, Tuple

import discord


class ConfirmView(discord.ui.View):
    """A confirm/cancel dialog with optional user restriction and callbacks.

    Parameters
    ----------
    user_id : int, optional
        If set, only this user may interact.
    on_confirm : Callable[[discord.Interaction], Awaitable[None]], optional
        Async callback invoked when the confirm button is pressed.
    on_cancel : Callable[[discord.Interaction], Awaitable[None]], optional
        Async callback invoked when the cancel button is pressed.
    timeout : float
        Seconds before the view times out (default: 60).
    confirm_label : str
        Text label for the confirm button (default: "Bestätigen").
    cancel_label : str
        Text label for the cancel button (default: "Abbrechen").
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        on_confirm: Optional[Callable[[discord.Interaction], Awaitable[None]]] = None,
        on_cancel: Optional[Callable[[discord.Interaction], Awaitable[None]]] = None,
        timeout: float = 60.0,
        confirm_label: str = "Bestätigen",
        cancel_label: str = "Abbrechen",
    ) -> None:
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self.value: Optional[bool] = None

        self.confirm_btn = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label=confirm_label,
            emoji="✅",
            custom_id="confirm_yes",
        )
        self.confirm_btn.callback = self._confirm

        self.cancel_btn = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label=cancel_label,
            emoji="❌",
            custom_id="confirm_no",
        )
        self.cancel_btn.callback = self._cancel

        self.add_item(self.confirm_btn)
        self.add_item(self.cancel_btn)

    # ── Callbacks ─────────────────────────────────────────────────────────

    async def _confirm(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.value = True
        if self._on_confirm:
            await self._on_confirm(interaction)
        else:
            await interaction.response.edit_message(view=None)
        self.stop()

    async def _cancel(self, interaction: discord.Interaction) -> None:
        if self._check_user(interaction):
            return
        self.value = False
        if self._on_cancel:
            await self._on_cancel(interaction)
        else:
            await interaction.response.edit_message(view=None)
        self.stop()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _check_user(self, interaction: discord.Interaction) -> bool:
        """Return True if the user is not allowed to interact."""
        return self.user_id is not None and interaction.user.id != self.user_id

    async def on_timeout(self) -> None:
        self.stop()


class ChoiceView(discord.ui.View):
    """Present up to 4 labelled buttons and track which was selected.

    Parameters
    ----------
    options : list[tuple[str, str]]
        List of (label, custom_id) pairs for each button. At most 4.
    user_id : int, optional
        If set, only this user may interact.
    timeout : float
        Seconds before the view times out (default: 60).
    """

    MAX_BUTTONS = 4

    def __init__(
        self,
        options: List[Tuple[str, str]],
        user_id: Optional[int] = None,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.selected: Optional[str] = None

        if len(options) > self.MAX_BUTTONS:
            options = options[: self.MAX_BUTTONS]

        for label, custom_id in options:
            btn = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=label,
                custom_id=f"choice_{custom_id}",
            )
            btn.callback = self._make_callback(custom_id)
            self.add_item(btn)

    def _make_callback(self, choice_id: str):
        """Create a callback that records the selected choice."""

        async def callback(interaction: discord.Interaction) -> None:
            if self.user_id is not None and interaction.user.id != self.user_id:
                return
            self.selected = choice_id
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()

        return callback

    async def on_timeout(self) -> None:
        self.stop()
