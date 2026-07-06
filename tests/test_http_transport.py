from __future__ import annotations

from pathlib import Path
import unittest

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from projector.model import load_model
from projector.state import ProjectorState
from transports.http import HttpTransport


class HttpTransportJsonQueryShapeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "TW3200.json"
        self.model = load_model(model_path)
        self.state = ProjectorState(self.model)
        self.transport = HttpTransport(self.state, self.model)

        app = web.Application()
        app.router.add_get("/cgi-bin/json_query", self.transport._handle_json_query)
        self.server = TestServer(app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_json_query_success_contains_all_feature_attributes(self) -> None:
        response = await self.client.get(
            "/cgi-bin/json_query",
            params={"jsoncallback": "PWR?"},
        )

        self.assertEqual(response.status, 200)
        body = await response.json()
        feature = body["projector"]["feature"]

        self.assertEqual(set(feature), {"name", "query", "reply", "error"})
        self.assertEqual(feature["name"], "esc/vp21")
        self.assertEqual(feature["query"], "PWR?")
        self.assertEqual(feature["reply"], self.state.get("PWR"))
        self.assertFalse(feature["error"])

    async def test_json_query_malformed_command_contains_all_feature_attributes(self) -> None:
        response = await self.client.get(
            "/cgi-bin/json_query",
            params={"jsoncallback": "PWR"},
        )

        self.assertEqual(response.status, 200)
        body = await response.json()
        feature = body["projector"]["feature"]

        self.assertEqual(set(feature), {"name", "query", "reply", "error"})
        self.assertEqual(feature["name"], "esc/vp21")
        self.assertEqual(feature["query"], "PWR")
        self.assertEqual(feature["reply"], "ERR")
        self.assertTrue(feature["error"])


class HttpTransportDirectsendKeyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "TW3200.json"
        self.model = load_model(model_path)
        self.state = ProjectorState(self.model)
        self.transport = HttpTransport(self.state, self.model)
        self.logged: list[tuple[str, str, str]] = []
        self.state.add_command_observer(
            lambda transport, command, response: self.logged.append((transport, command, response))
        )

        app = web.Application()
        app.router.add_get("/cgi-bin/directsend", self.transport._handle_directsend)
        self.server = TestServer(app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_key_source_mapping_logs_received_key_command(self) -> None:
        response = await self.client.get(
            "/cgi-bin/directsend",
            params={"KEY": "40"},
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(self.state.get("SOURCE"), "A0")
        self.assertIn(("http", "KEY 40", ":"), self.logged)

    async def test_unknown_key_returns_bad_request_and_logs_received_command(self) -> None:
        response = await self.client.get(
            "/cgi-bin/directsend",
            params={"KEY": "ZZ"},
        )

        self.assertEqual(response.status, 400)
        self.assertIn(("http", "KEY ZZ", "ERR\r:"), self.logged)


class HttpTransportDirectsendVolumeKeyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        model_path = Path(__file__).resolve().parents[1] / "models" / "HC1100.json"
        self.model = load_model(model_path)
        self.state = ProjectorState(self.model)
        self.transport = HttpTransport(self.state, self.model)

        app = web.Application()
        app.router.add_get("/cgi-bin/directsend", self.transport._handle_directsend)
        self.server = TestServer(app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_key_volume_inc_dec(self) -> None:
        before = int(self.state.get("VOL") or "0")

        response_inc = await self.client.get(
            "/cgi-bin/directsend",
            params={"KEY": "56"},
        )
        self.assertEqual(response_inc.status, 200)
        after_inc = int(self.state.get("VOL") or "0")
        self.assertGreaterEqual(after_inc, before)

        response_dec = await self.client.get(
            "/cgi-bin/directsend",
            params={"KEY": "57"},
        )
        self.assertEqual(response_dec.status, 200)
        after_dec = int(self.state.get("VOL") or "0")
        self.assertLessEqual(after_dec, after_inc)


if __name__ == "__main__":
    unittest.main()
