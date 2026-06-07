## Why

The ESC/VP.net emulator session currently stays open indefinitely once CONNECT succeeds. Real-world clients and networks may drop stale sessions, and keeping inactive sockets forever can consume connection slots and resources.

Adding an inactivity timeout makes the emulator behavior more robust and predictable for long-running test environments.

## What Changes

- Add inactivity timeout enforcement to ESC/VP.net post-handshake sessions: if no data is received for 10 minutes, the transport closes the TCP connection
- Define inactivity as no incoming ESC/VP21 command bytes on a connected ESC/VP.net session
- Keep active sessions unaffected: any inbound command activity resets the inactivity timer
- Add tests covering timeout closure and timer reset behavior
- Make the timeout value configurable in code with a default of 600 seconds for ESC/VP.net transport

## Capabilities

### New Capabilities
- `vpnet-idle-timeout`: Inactivity timeout lifecycle management for connected ESC/VP.net sessions

### Modified Capabilities
- `vpnet-transport`: Post-CONNECT session behavior changes to include automatic disconnect after 10 minutes of inactivity

## Impact

- Affected code: `transports/vpnet.py`, potentially shared stream-loop helpers in `transports/base.py` if reused
- Affected tests: `tests/test_http_transport.py` is unaffected; new/updated VP.net transport tests will be required (likely a new VP.net transport test module)
- Runtime behavior: idle ESC/VP.net connections now close automatically after timeout
- APIs/dependencies: no external API changes and no new dependencies expected
