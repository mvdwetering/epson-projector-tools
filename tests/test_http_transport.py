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
        model_path = Path(__file__).resolve().parents[1] / "models" / "eh_tw3200.yaml"
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


if __name__ == "__main__":
    unittest.main()
