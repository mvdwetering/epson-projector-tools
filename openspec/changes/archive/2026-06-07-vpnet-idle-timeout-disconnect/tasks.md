## 1. VP.net timeout plumbing

- [x] 1.1 Add a VP.net idle-timeout constant/default (600 seconds) and constructor-level timeout parameter in transports/vpnet.py
- [x] 1.2 Update the post-CONNECT session loop to enforce inactivity timeout on inbound command reads
- [x] 1.3 Ensure idle timeout path closes the TCP writer cleanly and exits the session coroutine without protocol error frames

## 2. VP.net behavior validation tests

- [x] 2.1 Add or extend VP.net transport async tests to verify idle session disconnect when timeout elapses
- [x] 2.2 Add or extend VP.net transport async tests to verify inbound activity resets the timeout window
- [x] 2.3 Keep tests deterministic by injecting a short timeout value and avoiding long real-time waits

## 3. Regression and compatibility checks

- [x] 3.1 Verify existing VP.net handshake and command-response scenarios still pass with timeout logic enabled
- [x] 3.2 Run the relevant test suite and confirm no regressions in non-VP.net transports
- [x] 3.3 Document any follow-up work (for example CLI configurability or timeout disconnect logging) outside this change
