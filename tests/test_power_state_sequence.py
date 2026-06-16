from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from projector.engine import handle_command
from projector.model import load_model, ModelDef, CommandDef
from projector.power import PowerSequencer
from projector.state import ProjectorState

_MODELS = Path(__file__).resolve().parents[1] / "models"


def _make_state(pwr: str = "01") -> tuple[ProjectorState, ModelDef]:
    """Return a minimal state/model pair for power tests."""
    model = load_model(_MODELS / "TW3200.json")
    state = ProjectorState(model)
    state.set("PWR", pwr)
    return state, model


# ---------------------------------------------------------------------------
# 6.4 — Model parsing
# ---------------------------------------------------------------------------

class ModelParsingTests(unittest.TestCase):
    def test_ls11000_warmup_and_comms_standby(self) -> None:
        model = load_model(_MODELS / "LS11000.json")
        self.assertEqual(model.warmup_seconds, 30.0)
        self.assertTrue(model.supports_comms_standby)
        self.assertEqual(model.standby_state, "04")

    def test_ls11000_cooldown_normal(self) -> None:
        model = load_model(_MODELS / "LS11000.json")
        # "Normal" cooldown is 0 seconds per executionTimes
        self.assertEqual(model.cooldown_seconds, 0.0)

    def test_tw3200_no_comms_standby(self) -> None:
        model = load_model(_MODELS / "TW3200.json")
        self.assertFalse(model.supports_comms_standby)
        self.assertEqual(model.standby_state, "00")

    def test_tw3200_default_warmup_cooldown(self) -> None:
        # TW3200 has no executionTimes entries → defaults apply
        model = load_model(_MODELS / "TW3200.json")
        self.assertEqual(model.warmup_seconds, 5.0)
        self.assertEqual(model.cooldown_seconds, 3.0)


# ---------------------------------------------------------------------------
# 6.2 — PowerSequencer rejection scenarios
# ---------------------------------------------------------------------------

class PowerSequencerRejectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()

    def tearDown(self) -> None:
        self.loop.close()

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_request_on_rejected_during_warmup(self) -> None:
        state, model = _make_state("02")
        seq = PowerSequencer()
        result = seq.request_on(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "02")
        seq.cancel()

    def test_request_on_rejected_during_cooldown(self) -> None:
        state, model = _make_state("03")
        seq = PowerSequencer()
        result = seq.request_on(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "03")

    def test_request_on_rejected_when_already_on(self) -> None:
        state, model = _make_state("01")
        seq = PowerSequencer()
        result = seq.request_on(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "01")

    def test_request_off_rejected_during_warmup(self) -> None:
        state, model = _make_state("02")
        seq = PowerSequencer()
        result = seq.request_off(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "02")

    def test_request_off_rejected_during_cooldown(self) -> None:
        state, model = _make_state("03")
        seq = PowerSequencer()
        result = seq.request_off(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "03")

    def test_request_off_rejected_when_in_standby_00(self) -> None:
        state, model = _make_state("00")
        seq = PowerSequencer()
        result = seq.request_off(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "00")

    def test_request_off_rejected_when_in_standby_04(self) -> None:
        state, model = _make_state("04")
        seq = PowerSequencer()
        result = seq.request_off(state, model)
        self.assertFalse(result)
        self.assertEqual(state.get("PWR"), "04")

    def test_cancel_safe_when_idle(self) -> None:
        seq = PowerSequencer()
        seq.cancel()  # Should not raise
        self.assertFalse(seq.is_transitioning)


# ---------------------------------------------------------------------------
# 6.1 — PowerSequencer state progression
# ---------------------------------------------------------------------------

class PowerSequencerProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()

    def tearDown(self) -> None:
        self.loop.close()

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_power_on_sequence_00_to_warmup_to_normal(self) -> None:
        state, model = _make_state("00")
        # Use a model with very short delay
        model.warmup_seconds = 0.01

        seq = PowerSequencer()

        async def run():
            result = seq.request_on(state, model)
            self.assertTrue(result)
            self.assertEqual(state.get("PWR"), "02")
            await asyncio.sleep(0.05)
            self.assertEqual(state.get("PWR"), "01")

        self._run(run())

    def test_power_on_sequence_04_to_warmup_to_normal(self) -> None:
        state, model = _make_state("04")
        model.warmup_seconds = 0.01

        seq = PowerSequencer()

        async def run():
            result = seq.request_on(state, model)
            self.assertTrue(result)
            self.assertEqual(state.get("PWR"), "02")
            await asyncio.sleep(0.05)
            self.assertEqual(state.get("PWR"), "01")

        self._run(run())

    def test_power_off_sequence_to_standby_00(self) -> None:
        state, model = _make_state("01")
        model.cooldown_seconds = 0.01
        # TW3200 has no comms standby → standby_state = "00"

        seq = PowerSequencer()

        async def run():
            result = seq.request_off(state, model)
            self.assertTrue(result)
            self.assertEqual(state.get("PWR"), "03")
            await asyncio.sleep(0.05)
            self.assertEqual(state.get("PWR"), "00")

        self._run(run())

    def test_power_off_sequence_to_standby_04_on_comms_standby_model(self) -> None:
        model = load_model(_MODELS / "LS11000.json")
        state = ProjectorState(model)
        state.set("PWR", "01")
        model.cooldown_seconds = 0.01

        seq = PowerSequencer()

        async def run():
            result = seq.request_off(state, model)
            self.assertTrue(result)
            self.assertEqual(state.get("PWR"), "03")
            await asyncio.sleep(0.05)
            self.assertEqual(state.get("PWR"), "04")

        self._run(run())

    def test_cancel_aborts_warmup(self) -> None:
        state, model = _make_state("00")
        model.warmup_seconds = 10.0  # long enough not to complete

        seq = PowerSequencer()

        async def run():
            seq.request_on(state, model)
            self.assertEqual(state.get("PWR"), "02")
            seq.cancel()
            self.assertFalse(seq.is_transitioning)
            # Give event loop a tick — no further state change expected
            await asyncio.sleep(0.01)
            self.assertEqual(state.get("PWR"), "02")

        self._run(run())


# ---------------------------------------------------------------------------
# 6.3 — handle_command with sequencer
# ---------------------------------------------------------------------------

class HandleCommandWithSequencerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()

    def tearDown(self) -> None:
        self.loop.close()

    def _make_seq_accepted(self) -> PowerSequencer:
        seq = MagicMock(spec=PowerSequencer)
        seq.request_on.return_value = True
        seq.request_off.return_value = True
        return seq

    def _make_seq_rejected(self) -> PowerSequencer:
        seq = MagicMock(spec=PowerSequencer)
        seq.request_on.return_value = False
        seq.request_off.return_value = False
        return seq

    def test_pwr_on_accepted_returns_ok(self) -> None:
        state, model = _make_state("00")
        seq = self._make_seq_accepted()
        response = handle_command(state, model, "PWR ON", seq)
        self.assertEqual(response, ":")
        seq.request_on.assert_called_once_with(state, model)

    def test_pwr_off_accepted_returns_ok(self) -> None:
        state, model = _make_state("01")
        seq = self._make_seq_accepted()
        response = handle_command(state, model, "PWR OFF", seq)
        self.assertEqual(response, ":")
        seq.request_off.assert_called_once_with(state, model)

    def test_pwr_on_rejected_returns_err(self) -> None:
        state, model = _make_state("02")
        seq = self._make_seq_rejected()
        response = handle_command(state, model, "PWR ON", seq)
        self.assertEqual(response, "ERR\r:")

    def test_pwr_off_rejected_returns_err(self) -> None:
        state, model = _make_state("03")
        seq = self._make_seq_rejected()
        response = handle_command(state, model, "PWR OFF", seq)
        self.assertEqual(response, "ERR\r:")

    def test_no_sequencer_pwr_on_synchronous(self) -> None:
        state, model = _make_state("00")
        response = handle_command(state, model, "PWR ON")
        self.assertEqual(response, ":")
        self.assertEqual(state.get("PWR"), "01")

    def test_no_sequencer_pwr_off_synchronous(self) -> None:
        state, model = _make_state("01")
        response = handle_command(state, model, "PWR OFF")
        self.assertEqual(response, ":")
        self.assertEqual(state.get("PWR"), "00")


if __name__ == "__main__":
    unittest.main()
