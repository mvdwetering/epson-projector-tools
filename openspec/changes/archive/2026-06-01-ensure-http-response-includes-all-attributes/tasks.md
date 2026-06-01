## 1. HTTP Response Shape Refactor

- [x] 1.1 Identify all `json_query` response code paths in [transports/http.py](transports/http.py) for success and error handling.
- [x] 1.2 Introduce/reuse a single response-construction helper that always emits `projector.feature.name`, `query`, `reply`, and `error`.
- [x] 1.3 Update `json_query` handling to route both success and ESC/VP21 error outcomes through the canonical response builder.

## 2. Behavior Validation

- [x] 2.1 Add or update tests for successful `json_query` responses to assert all required feature attributes are present.
- [x] 2.2 Add or update tests for malformed/error `json_query` responses (e.g., missing `?`) to assert all required attributes remain present with `reply="ERR"` and `error=true`.
- [x] 2.3 Run the test suite relevant to HTTP transport and fix any regressions introduced by the response-shape change.

## 3. Documentation and Verification

- [x] 3.1 Update protocol docs/examples if needed so success and error JSON examples both show the complete attribute set.
- [x] 3.2 Verify OpenSpec artifacts remain consistent (proposal, design, specs, tasks) and ready for `/opsx:apply`.
