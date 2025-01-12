#!/usr/bin/env python3

"""
Simple socket server to test without a real ESC/VP21 device

It is intended to be just enough to test without a real device

NOTE: 
* Does not take powered state into account
* Does not validate input values, just stores them!
* Does not validate INC/DEC capabilities
* Only values for EH-TW3200 are supported
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
import re
import socketserver
from typing import Dict, Tuple

@dataclass
class EscVp21Command:
    command: str
    value: str | None


def line_to_command(line) -> EscVp21Command | None:
    match = re.match(r"(?P<command>.+?) (?P<value>.*)", line)
    if match is not None:
        command = match.group("command")
        value = match.group("value")
        return EscVp21Command(command, value)
    match = re.match(r"(?P<command>.+?)\?", line)
    if match is not None:
        command = match.group("command")
        return EscVp21Command(command, None)
    return None


class EscVp21DataStore:
    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    def add_data(self, command, value):
        self._store[command] = value

    def get_data(self, command):
        try:
            value = self._store[command]
        except KeyError:
            return None
        return value

    def set_data(self, command, new_value) -> bool:
        """Write new value, returns True if value was stored, False if not"""
        if command in self._store:
            if new_value is not None:
                self._store[command] = new_value
            return True
        return False

class EscpVp21CommandHandler(socketserver.StreamRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    # ESC/VP21 does not seem to have a timeout?
    # Keep the line commented because it was hard to figure out how to make it work
    #timeout = 40  # Receiver disconnects after 40 seconds of no traffic

    def __init__(self, request, client_address, server: EscVp21Server):
        self.store = server.store
        self.disconnect_after_receiving_num_commands = (
            server.disconnect_after_receiving_num_commands
        )
        self.disconnect_after_sending_num_commands = (
            server.disconnect_after_sending_num_commands
        )
        self._commands_sent = 0
        super().__init__(request, client_address, server)

    def _write_response(self, line: str):
        print(f"Send - {line}")
        line += "\r"
        self.wfile.write(line.encode("utf-8"))
        self._commands_sent += 1

    def _write_colon(self):
        print("Send - :")
        self.wfile.write(":".encode("utf-8"))
        self.wfile.flush()

    def _send_value(self, command, value):
        """Just formats and send the value"""
        self._write_response(f"{command}={value}")

    def _send_error(self):
        """Just formats and send the value"""
        self._write_response("ERR")


    def handle_get(self, command):
        """Gets one value and writes the response to the socket"""
        value = self.store.get_data(command)
        logging.debug(f"Got value {value} for command {command}")
        if value is None:
            self._send_error()
        else:
            self._send_value(command, value)
        self._write_colon()

    def handle_set(self, command, value):

        if value == "INC" or value == "DEC":
            # TODO: Range checking
            amount = 1 if value == "INC" else -1

            # Assumption is all inc/dec commands are integers
            value = int(self.store.get_data(command))
            value = str(value + amount)

        # Quick hack, INIT is a special value and should not get stored
        if value == "INIT":
            value = None

        if command == "PWR":
            # TODO: Should be extended to emulate power states
            if value == "ON":
                value = "01"  # Lamp ON
            elif value == "OFF":
                value = "00"  # Standby Mode (Network OFF)

        # Store new value, will check for valid commands
        if not self.store.set_data(command, value):
            self._send_error()
        self._write_colon()

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        #
        # Note that the connection is closed when this handler returns!

        commands_received = 0

        print(f"--- Client connected from: {self.client_address[0]}")
        while True:
            try:
                # Read until \r which does not work with readline
                # bytes_line = self.rfile.readline()
                bytes_line = bytes()
                while byte := self.rfile.read(1):
                    bytes_line += byte
                    if byte == b"\r":
                        break

                if bytes_line == b"":
                    print("--- Client disconnected")
                    print("--- Waiting for connections")
                    return
            except TimeoutError:
                print("--- Disconnecting client because of timeout")
                print("--- Waiting for connections")
                return

            bytes_line = bytes_line.strip()
            line = bytes_line.decode(
                "utf-8"
            )  # Not sure if it is UTF-8, bue lets assume...
            print(f"Recv - {line}")

            # Empty command is called "null command". Can be used to check if is projector is operational
            if line == "":
                self._write_colon()
                continue

            command = line_to_command(line)
            if command is not None:
                if command.value is None:
                    self.handle_get(command.command)
                else:
                    self.handle_set(command.command, command.value)

            commands_received += 1
            if (
                self.disconnect_after_receiving_num_commands is not None
                and commands_received >= self.disconnect_after_receiving_num_commands
            ):
                print(
                    f"--- Disconnecting because of `disconnect_after_receiving_num_commands` limit {self.disconnect_after_receiving_num_commands} reached"
                )
                return

            if (
                self.disconnect_after_sending_num_commands is not None
                and self._commands_sent >= self.disconnect_after_sending_num_commands
            ):
                print(
                    "--- Disconnecting because of `disconnect_after_sending_num_commands` {self.disconnect_after_sending_num_commands} limit reached"
                )
                return


class EscVp21Server(socketserver.TCPServer):
    def __init__(
        self,
        server_address: Tuple[str, int],
        disconnect_after_receiving_num_commands=None,
        disconnect_after_sending_num_commands=None,
    ) -> None:
        self.allow_reuse_address = True
        super().__init__(server_address, EscpVp21CommandHandler)

        self.store = EscVp21DataStore()
        self.disconnect_after_receiving_num_commands = (
            disconnect_after_receiving_num_commands
        )
        self.disconnect_after_sending_num_commands = (
            disconnect_after_sending_num_commands
        )

        if disconnect_after_receiving_num_commands is not None:
            print(
                f"--- Each connection will be disconnected after receiving {disconnect_after_receiving_num_commands} commands!"
            )
        if disconnect_after_sending_num_commands is not None:
            print(
                f"--- Each connection will be disconnected after sending {disconnect_after_sending_num_commands} commands!"
            )

        # Add some data as supported by EH-TW3200
        # Note that on a real device only PWR, SNO and LAMP can be read when in STANDBY, others return ERR

        # TODO: PWR command SET has values ON/OFF which is different from GET and is currently not supported
        self.store.add_data("PWR", "01")  # Lamp ON
        # TODO: KEY is SET only, skipped for now
        self.store.add_data("ASPECT", "00")  # Normal
        self.store.add_data("LUMINANCE", "00")
        self.store.add_data("SOURCE", "30")  # HDMI1
        self.store.add_data("BRIGHT", "11")
        self.store.add_data("CONTRAST", "22")
        self.store.add_data("TINT", "33")
        # TODO: Check how SHARP looks on real device, spec is a bit unclear. Seems like we can't just store the value we get
        self.store.add_data("SHARP", "44")  
        self.store.add_data("CTEMP", "55")  
        self.store.add_data("FCOLOR", "66")  
        self.store.add_data("CMODE", "15")  # Cinema
        self.store.add_data("HPOS", "77")  
        self.store.add_data("VPOS", "88")  
        self.store.add_data("TRACKIOK", "99")  
        self.store.add_data("SYNC", "111")  
        self.store.add_data("OFFSETR", "122")  
        self.store.add_data("OFFSETG", "133")  
        self.store.add_data("OFFSETB", "144")  
        self.store.add_data("GAINR", "155")  
        self.store.add_data("GAING", "166")  
        self.store.add_data("GAINB", "177")  
        # TODO: Check how GAMMLV works on real device, spec is a bit unclear. Seems like we can't just store the value we get
        self.store.add_data("GAMMALV", "188")  
        # POPMEM, PUSHMEM and ERASEMEM are SET only, is not supported for now
        # TODO: CSEL is GET only
        self.store.add_data("CSEL", "07") # RGB/RGBCMY 
        self.store.add_data("MUTE", "OFF")  
        self.store.add_data("HREVERSE", "OFF")  
        self.store.add_data("VREVERSE", "OFF")  
        self.store.add_data("MSEL", "00")  # Black background
        # INITALL has no parameter, is not supported for now (and I am not going to try this out on my real projector)
        self.store.add_data("SPEED", "00")  # 9600bps, wow really... you can change the speed?
        # TODO: LAMP is GET only
        self.store.add_data("LAMP", "1234")
        # SNO is undocumented, but returns a serial number. Obviously GET only
        self.store.add_data("SNO", "NPCF1Y0202L")



def main(args):
    print(__doc__)

    with EscVp21Server(
        (args.host, args.port),
        args.disconnect_after_receiving_num_commands,
        args.disconnect_after_sending_num_commands,
    ) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C

        print("--- Waiting for connections")

        server.timeout = None
        server.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="ESC/VP21 server to emulate a device for basic testing."
    )

    parser.add_argument(
        "--host",
        help="Host interface to bind to, default is 0.0.0.0 for all interfaces",
        default="0.0.0.0",
    )
    parser.add_argument(
        "--port",
        help="Port to use, default is 12345",
        default=12345,
        type=int,
    )
    parser.add_argument(
        "--disconnect_after_receiving_num_commands",
        help="Disconnect after receiving this amount of commands, useful for testing disconnects",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--disconnect_after_sending_num_commands",
        help="Disconnect after sending this amount of commands, useful for testing disconnects",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Define loglevel, default is INFO.",
    )

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    main(args)
