## Context

ESC/VP.net is a binary protocol that wraps the text-based ESC/VP21 command set for network delivery. The handshake phase uses 16-byte binary packets; after session establishment the stream reverts to plain ESC/VP21 text commands. Debugging connection failures or command-level issues in Wireshark today means reading raw hex with no field labels.

A Wireshark Lua dissector plugin will label every field in every packet, making session traces immediately readable without manual hex parsing.

This design covers only the dissector — no changes to the emulator codebase.

## Goals / Non-Goals

**Goals:**
- Decode all ESC/VP.net binary header fields (HELLO, PASSWORD, CONNECT and their responses)
- Display the ESC/VP21 text payload after session establishment
- Register automatically on TCP port 3629 and support manual "Decode As" assignment
- Operate as a single, self-contained `.lua` file placed in the Wireshark plugins directory

**Non-Goals:**
- Decoding ESC/VP21 commands beyond presenting them as labelled ASCII text (that is a separate dissector concern)
- Supporting UDP transport
- Modifying or depending on any Python emulator code
- Handling ESC/VP.net command specifications (SNMP, mail, WLAN config) sent after session establishment — those travel as ESC/VP21 text and are out of scope

## Decisions

### Decision 1: Single-file Lua plugin

**Choice**: Deliver one file (`dissectors/escvpnet.lua`) with no external dependencies.

**Rationale**: Wireshark Lua plugins are dropped into a directory and loaded automatically; a single file minimises installation friction. The protocol is small enough that no modular split is warranted.

**Alternatives considered**: A multi-file plugin with a shared utilities module — unnecessary complexity for this scope.

---

### Decision 2: Stateful TCP stream tracking for phase detection

**Choice**: Use a per-stream state table (keyed on `pinfo.conversation`) to track whether the handshake is complete. Once a valid CONNECT response is seen, subsequent bytes in that stream are treated as ESC/VP21 text.

**Rationale**: ESC/VP.net overloads one TCP connection for two distinct formats. Without per-conversation state the dissector cannot know when to switch from binary to text mode.

**Alternatives considered**: Heuristic detection (look for ESC/VP21 greeting bytes) — fragile and spec-non-compliant; rejected in favour of following the handshake state machine explicitly.

---

### Decision 3: Header identified by magic string "ESC/VP.net"

**Choice**: The dissector uses the 10-byte magic `"ESC/VP.net"` at the start of each handshake packet to confirm it is looking at a valid message before parsing further fields.

**Rationale**: The specification defines this fixed prefix; checking it guards against dissecting unrelated TCP traffic on the same port.

---

### Decision 4: Wireshark `DissectorTable` for ESC/VP21 handoff

**Choice**: After session establishment, call `Dissector.get("data-text-lines")` (or a dedicated ESC/VP21 dissector if registered) to display the text payload.

**Rationale**: Keeps the ESC/VP.net dissector focused on the handshake. Using a named dissector table follows Wireshark best practices and allows a future ESC/VP21 dissector to be chained automatically.

## Risks / Trade-offs

- **TCP segmentation** → Wireshark's `DissectorTable` and `tvb:len()` checks handle partial packets; the dissector should check that at least 16 bytes are available before parsing a handshake message.
- **Wireshark Lua API version drift** → The dissector targets the Wireshark 3.x / 4.x Lua API. Field type names are stable across those versions.
- **Password payload contents** → The PASSWORD message carries credential data. The dissector will label the field but display it as raw bytes to avoid accidentally surfacing passwords in screenshots. No masking is applied beyond labelling the field `password_data`.
- **Port conflicts** → If another application uses port 3629, the dissector will attempt to parse its traffic. The magic-string guard (Decision 3) prevents incorrect field labelling but cannot suppress the dissector registration.

## Open Questions

- Should the dissector attempt to decode the `num_headers` / variable-length header extension area described in the specification, or label it as `reserved_extension`? (Recommendation: label as opaque bytes for now; spec indicates this field is rarely non-zero in practice.)
