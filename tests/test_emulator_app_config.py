from __future__ import annotations

import asyncio
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
        model_path = Path(__file__).resolve().parents[1] / "models" / "TW3200.json"
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
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            ),
            password_store=PasswordStore("emulatorpassword", enabled=False),
        )

        async with app.run_test():
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(table.get_cell("serial", "line"), "Serial TCP 12345")
            self.assertEqual(
                table.get_cell("vpnet", "line"),
                "ESC/VP.net  3629 🔓 !",
            )
            self.assertEqual(
                table.get_cell("http", "line"),
                "HTTP        8080 🔓 !",
            )

    async def test_config_panel_shows_overridden_ports_and_required_auth(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=15000,
                vpnet_port=4600,
                http_port=9000,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            ),
            password_store=PasswordStore("emulatorpassword", enabled=True),
        )

        async with app.run_test():
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(table.get_cell("serial", "line"), "Serial TCP 15000")
            self.assertEqual(
                table.get_cell("vpnet", "line"),
                "ESC/VP.net  4600 🔒 !",
            )
            self.assertEqual(
                table.get_cell("http", "line"),
                "HTTP        9000 🔒 !",
            )
            self.assertNotIn("emulatorpassword", table.get_cell("http", "line"))

    async def test_connection_info_panel_is_above_state_panel(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        async with app.run_test():
            left_panel = app.query_one("#left-panel", Vertical)
            order = [child.id for child in left_panel.children]
            self.assertEqual(order, ["config-table", "state-table"])

    async def test_toggle_auth_action_updates_auth_icons(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            ),
            password_store=PasswordStore("emulatorpassword", enabled=False),
        )

        async with app.run_test() as pilot:
            table: DataTable = app.query_one("#config-table", DataTable)
            self.assertEqual(
                table.get_cell("vpnet", "line"),
                "ESC/VP.net  3629 🔓 !",
            )
            await pilot.press("a")
            self.assertEqual(
                table.get_cell("vpnet", "line"),
                "ESC/VP.net  3629 🔒 !",
            )
            self.assertEqual(
                table.get_cell("http", "line"),
                "HTTP        8080 🔒 !",
            )

    async def test_state_table_uses_pinned_then_recent_then_alphabetical_order(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        async with app.run_test():
            table: DataTable = app.query_one("#state-table", DataTable)
            initial_order = [str(key.value) for key in table.rows.keys()]
            pinned_expected = [
                cmd for cmd in ["PWR", "SOURCE", "SNO", "LAMP", "KEY"] if cmd in initial_order
            ]
            self.assertEqual(initial_order[: len(pinned_expected)], pinned_expected)

            app._mark_command_recent("BRIGHT")
            app._mark_command_recent("ASPECT")
            app._build_state_table()

            new_order = [str(key.value) for key in table.rows.keys()]
            self.assertEqual(
                new_order[: len(pinned_expected) + 2],
                pinned_expected + ["ASPECT", "BRIGHT"],
            )

    async def test_switch_model_reloads_state_and_updates_title(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )
        model_path = Path(__file__).resolve().parents[1] / "models" / "HC980.json"

        async with app.run_test():
            await app._switch_model(model_path)
            table: DataTable = app.query_one("#state-table", DataTable)
            row_keys = [str(key.value) for key in table.rows.keys()]

            self.assertIn("HC980.json", app.title)
            self.assertIn("VOL", row_keys)

    async def test_source_value_updates_to_a0_in_state_table(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        async with app.run_test():
            from projector.engine import handle_command

            handle_command(app._state, app._model, "SOURCE A0")
            await asyncio.sleep(0.05)

            table: DataTable = app.query_one("#state-table", DataTable)
            self.assertEqual(table.get_cell("SOURCE", "value"), "A0")

    async def test_decimal_values_display_without_leading_zeroes(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        async with app.run_test():
            table: DataTable = app.query_one("#state-table", DataTable)
            self.assertEqual(table.get_cell("BRIGHT", "value"), "0")
            self.assertEqual(table.get_cell("CONTRAST", "value"), "0")

    async def test_model_picker_enter_applies_highlighted_model(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        async with app.run_test() as pilot:
            before_title = app.title
            await pilot.press("m")
            await pilot.press("enter")
            await pilot.pause()

            self.assertNotEqual(app.title, before_title)
            self.assertIn(".json", app.title)

    async def test_stop_transports_calls_transport_cleanup(self) -> None:
        app = self._make_app(
            EmulatorRuntimeConfig(
                host="127.0.0.1",
                serial_port=12345,
                vpnet_port=3629,
                http_port=8080,
                models_dir=Path(__file__).resolve().parents[1] / "models",
            )
        )

        class DummyTransport:
            def __init__(self) -> None:
                self.stopped = False

            async def start(self) -> None:
                await asyncio.sleep(0)

            async def stop(self) -> None:
                self.stopped = True

        dummy = DummyTransport()
        app._transports = [dummy]  # type: ignore[assignment]
        app._transport_tasks = [asyncio.create_task(dummy.start())]

        await app._stop_transports()

        self.assertTrue(dummy.stopped)
        self.assertEqual(app._transport_tasks, [])


if __name__ == "__main__":
    unittest.main()
