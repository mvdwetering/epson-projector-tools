from __future__ import annotations

from pathlib import Path
import unittest

from projector.engine import handle_command
from projector.model import load_model
from projector.state import ProjectorState


class JsonModelLoaderTests(unittest.TestCase):
    def test_loads_model_metadata_and_aggregates_command_constraints(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "HC980.json"
        model = load_model(model_path)

        self.assertEqual(model.file_name, "HC980.json")
        self.assertGreater(len(model.sources), 0)
        self.assertGreater(len(model.ir_codes), 0)

        source_cmd = model.commands["SOURCE"]
        self.assertIsNotNone(source_cmd.set_values)
        self.assertEqual(set(source_cmd.set_values or []), model.source_codes())

        key_cmd = model.commands["KEY"]
        self.assertTrue(key_cmd.notify_only)
        self.assertEqual(set(key_cmd.set_values or []), model.ir_codes)

    def test_sno_exists_for_models_even_if_not_explicitly_defined(self) -> None:
        tw = load_model(Path(__file__).resolve().parents[1] / "models" / "TW3200.json")
        self.assertIn("SNO", tw.commands)
        self.assertTrue(tw.commands["SNO"].readable)
        self.assertFalse(tw.commands["SNO"].writable)
        self.assertEqual(len(tw.commands["SNO"].default), 11)

    def test_sourcelist_supported_only_when_command_present(self) -> None:
        tw = load_model(Path(__file__).resolve().parents[1] / "models" / "TW3200.json")
        ls = load_model(Path(__file__).resolve().parents[1] / "models" / "LS11000.json")
        self.assertNotIn("SOURCELIST", tw.commands)
        self.assertIn("SOURCELIST", ls.commands)


class JsonEngineBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "HC1100.json"
        self.model = load_model(model_path)
        self.state = ProjectorState(self.model)

    def test_sourcelist_and_sourcelista_return_same_non_cyclic_sources(self) -> None:
        resp_list = handle_command(self.state, self.model, "SOURCELIST?")
        resp_lista = handle_command(self.state, self.model, "SOURCELISTA?")

        self.assertTrue(resp_list.startswith("SOURCELIST="))
        self.assertEqual(
            resp_list.replace("SOURCELIST=", ""),
            resp_lista.replace("SOURCELISTA=", ""),
        )
        # Cyclic entries must not appear in payload.
        self.assertNotIn("F0", resp_list)
        self.assertNotIn("F1", resp_list)
        self.assertNotIn("F2", resp_list)

    def test_sourcelist_returns_err_when_not_supported_by_model(self) -> None:
        tw_model = load_model(Path(__file__).resolve().parents[1] / "models" / "TW3200.json")
        tw_state = ProjectorState(tw_model)
        self.assertEqual(handle_command(tw_state, tw_model, "SOURCELIST?"), "ERR\r:")
        self.assertEqual(handle_command(tw_state, tw_model, "SOURCELISTA?"), "ERR\r:")

    def test_null_command_returns_colon_only_ack(self) -> None:
        self.assertEqual(handle_command(self.state, self.model, "\r"), ":")

    def test_source_parameter_is_validated_against_model_sources(self) -> None:
        valid_source = next(iter(self.model.source_codes()))
        ok = handle_command(self.state, self.model, f"SOURCE {valid_source}")
        err = handle_command(self.state, self.model, "SOURCE ZZ")

        self.assertEqual(ok, ":")
        self.assertEqual(err, "ERR\r:")

    def test_key_parameter_is_validated_against_ir_codes(self) -> None:
        valid_key = next(iter(self.model.ir_codes))
        ok = handle_command(self.state, self.model, f"KEY {valid_key}")
        err = handle_command(self.state, self.model, "KEY ZZ")

        self.assertEqual(ok, ":")
        self.assertEqual(err, "ERR\r:")

    def test_inc_dec_only_applies_to_decimal_single_parameter_commands(self) -> None:
        self.assertEqual(handle_command(self.state, self.model, "VOL 10"), ":")
        self.assertEqual(handle_command(self.state, self.model, "VOL INC"), ":")
        self.assertEqual(self.state.get("VOL"), "11")

        # SMODE is not a decimal single-parameter INC/DEC command in this milestone.
        self.assertEqual(handle_command(self.state, self.model, "SMODE INC"), "ERR\r:")

    def test_pwr_query_returns_protocol_code_value(self) -> None:
        self.assertEqual(handle_command(self.state, self.model, "PWR OFF"), ":")
        self.assertEqual(handle_command(self.state, self.model, "PWR?"), "PWR=00\r:")
        self.assertEqual(handle_command(self.state, self.model, "PWR ON"), ":")
        self.assertEqual(handle_command(self.state, self.model, "PWR?"), "PWR=01\r:")

    def test_sno_and_lamp_have_non_zero_defaults(self) -> None:
        self.assertEqual(
            handle_command(self.state, self.model, "SNO?"),
            f"SNO={self.model.commands['SNO'].default}\r:",
        )
        self.assertEqual(handle_command(self.state, self.model, "LAMP?"), "LAMP=1234\r:")

    def test_projector_state_normalizes_invalid_source_default(self) -> None:
        model = load_model(Path(__file__).resolve().parents[1] / "models" / "HC980.json")
        model.commands["SOURCE"].default = "ZZ"
        state = ProjectorState(model)

        self.assertIn(state.get("SOURCE"), model.source_codes())


if __name__ == "__main__":
    unittest.main()
