## 1. Engine acknowledgment behavior

- [x] 1.1 Locate null-command handling path in `projector/engine.py` and update it to return `:` for plain `\r` input.
- [x] 1.2 Update successful SET acknowledgment response construction to return `:` while preserving existing error framing.
- [x] 1.3 Verify query and error response formatting code paths are unchanged.

## 2. Test updates

- [x] 2.1 Update or add unit tests for null-command input to assert response `:`.
- [x] 2.2 Update SET-success test expectations to assert response `:` for normal and INC/DEC success paths.
- [x] 2.3 Confirm negative SET scenarios still assert `ERR\r:`.

## 3. Validation

- [x] 3.1 Run targeted tests for engine and transport-visible command behavior.
- [x] 3.2 Review test output for regressions unrelated to acknowledgment framing and document any follow-up.
