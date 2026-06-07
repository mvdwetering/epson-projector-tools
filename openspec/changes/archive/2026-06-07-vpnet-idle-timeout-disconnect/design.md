## Context

ESC/VP.net connections currently remain active indefinitely after a successful CONNECT handshake and transition into ESC/VP21 command mode. In long-running emulator sessions, this can leave stale sockets open when clients disappear silently (network interruptions, ungraceful process exit, idle controller behavior).

The transport is implemented in `transports/vpnet.py` and reuses a stream-processing loop pattern also used by serial transport. The desired behavior is specific to VP.net sessions after handshake: close the connection after 10 minutes of no inbound activity.

## Goals / Non-Goals

**Goals:**
- Enforce a 10-minute inactivity timeout for connected VP.net sessions
- Reset the inactivity timer whenever inbound ESC/VP21 command data is received
- Keep active clients unaffected while ensuring stale sessions are cleaned up
- Add tests that validate timeout closure and timeout reset behavior

**Non-Goals:**
- Add protocol-level keepalive packets or heartbeat negotiation
- Introduce a user-facing CLI flag for timeout customization in this change
- Change serial transport or HTTP transport timeout behavior
- Modify handshake semantics before CONNECT succeeds

## Decisions

### D1: Enforce inactivity timeout in the VP.net post-handshake read loop

Use an asyncio read timeout around command reads once CONNECT has succeeded. If the timeout elapses without inbound bytes, close the writer and end the session coroutine.

Alternative considered: background watchdog task tracking last activity timestamps. Rejected because it adds shared mutable state and cancellation complexity for little benefit over timeout-aware reads.

### D2: Keep timeout value as a transport constant with a default of 600 seconds

Define a VP.net idle timeout default in transport code (600 seconds), with constructor-level configurability for tests and future extension.

Alternative considered: hardcode literal values in read calls. Rejected for readability and testability.

Alternative considered: add immediate CLI/config plumbing. Rejected to keep scope focused on behavior and test coverage.

### D3: Treat inbound command bytes as activity; response writes do not reset timeout

The timeout is defined by client activity, so only successful incoming command reads reset the timer. Outbound responses are a consequence of inbound commands and do not independently extend idle lifetime.

Alternative considered: reset on any socket I/O. Rejected because it could keep one-way noisy sessions alive without client command activity.

### D4: Close idle session cleanly without emitting protocol error frames

On timeout, simply close the TCP connection. No ESC/VP.net status frame is sent because the session is already in raw ESC/VP21 pipe mode after CONNECT.

Alternative considered: send an ESC/VP21 ERR before close. Rejected because timeout is transport lifecycle behavior, not command failure.

## Risks / Trade-offs

- Timing-sensitive tests can be flaky if they rely on real 600-second waits -> Mitigation: inject a small timeout value in tests and use deterministic async waits
- Some clients may assume persistent sockets forever -> Mitigation: behavior is predictable and clients can reconnect automatically
- Timeout logic may diverge from shared stream-loop behavior -> Mitigation: keep implementation localized and covered by VP.net-specific tests
- Potential accidental timeout before first command after CONNECT in slow clients -> Mitigation: timeout window is long (10 minutes) by default

## Migration Plan

- No data migration required
- Runtime behavior changes immediately when deploying updated transport code
- Rollback strategy: revert VP.net transport timeout change to restore previous indefinite-session behavior

## Open Questions

- Should timeout value become CLI-configurable in a follow-up change for integration test environments?
- Should we log explicit timeout-disconnect events in the emulator UI command log for observability?
