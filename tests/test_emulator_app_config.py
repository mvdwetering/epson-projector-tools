from __future__ import annotations

import unittest
from pathlib import Path

from textual.containers import Vertical
from textual.widgets import DataTable

from projector.model import load_model
from projector.state import ProjectorState
from transports.http import PasswordStore
from ui.app import EmulatorApp, EmulatorRuntimeConfig


class EmulatorAppConfigPanelTests(unittest.IsolatedAsyncioTestCase):
    def _make_app(
        self,
        runtime_config: EmulatorRuntimeConfig,
        password_store: PasswordStore | None = None,
    ) -> EmulatorApp:
        model_path = Path(__file__).resolve().parents[1] / "models" / "eh_tw3200.yaml"
        model = load_model(model_path)
        state = ProjectorState(model)
        return EmulatorApp(
            state=state,
            model=model,
            transports=[],
            runtime_config=runtime_config,
            password_store=password_store,
        )

    async def test_config_panel_shows_default_ports_and_auth_not_required(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
            ),
            password_store=PasswordStore("emulatorpassword", enabled=False),
        )

        async with app.run_test():
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(table.get_cell("serial", "line"), "Serial TCP 12345")
            self.assertEqual(table.get_cell("vpnet", "line"), "ESC/VP.net  3629 🔓")
            self.assertEqual(table.get_cell("http", "line"), "HTTP        8080 🔓")

    async def test_config_panel_shows_overridden_ports_and_required_auth(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                serial_port=15000,
                vpnet_port=4600,
                http_port=9000,
            ),
            password_store=PasswordStore("emulatorpassword", enabled=True),
        )

        async with app.run_test():
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(table.get_cell("serial", "line"), "Serial TCP 15000")
            self.assertEqual(table.get_cell("vpnet", "line"), "ESC/VP.net  4600 🔒")
            self.assertEqual(table.get_cell("http", "line"), "HTTP        9000 🔒")
            self.assertNotIn("emulatorpassword", table.get_cell("http", "line"))

    async def test_connection_info_panel_is_above_state_panel(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
            )
        )

        async with app.run_test():
            left_panel = app.query_one("#left-panel", Vertical)
            order = [child.id for child in left_panel.children]
            self.assertEqual(order, ["config-table", "state-table"])

    async def test_toggle_auth_action_updates_auth_icons(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
            ),
            password_store=PasswordStore("emulatorpassword", enabled=False),
        )

        async with app.run_test() as pilot:
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(table.get_cell("vpnet", "line"), "ESC/VP.net  3629 🔓")
            await pilot.press("a")
            self.assertEqual(table.get_cell("vpnet", "line"), "ESC/VP.net  3629 🔒")
            self.assertEqual(table.get_cell("http", "line"), "HTTP        8080 🔒")


if __name__ == "__main__":
    unittest.main()
