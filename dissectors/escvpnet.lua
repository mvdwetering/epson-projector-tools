-- escvpnet.lua — Wireshark Lua dissector for the ESC/VP.net protocol
-- Protocol:  ESC/VP.net (SEIKO EPSON projector network control)
-- Ports:     TCP 3629  — session mode   (PASSWORD / CONNECT → ESC/VP21)
--            UDP 3629  — session-less mode (HELLO discovery broadcast)
-- Reference: ESC/VP.net Software Development Manual (SEIKO EPSON)
-- Wireshark Lua API: 3.x / 4.x
--
-- Installation: Copy to your Wireshark personal plugins directory.
--   Linux:   ~/.config/wireshark/plugins/
--   macOS:   ~/.local/lib/wireshark/plugins/
--   Windows: %APPDATA%\Wireshark\plugins\
-- Restart Wireshark. The dissector auto-registers on TCP/UDP port 3629.
-- It can also be applied manually via "Decode As → escvpnet".

-- ─── Constants ────────────────────────────────────────────────────────────────

local ESCVPNET_PORT = 3629
local MAGIC         = "ESC/VP.net"   -- 10 bytes: 45 53 43 2F 56 50 2E 6E 65 74
local MAGIC_LEN     = 10
local HEADER_LEN    = 16             -- fixed base header size (bytes)
local EXT_HDR_LEN   = 18            -- each extension header: 1 id + 1 attr + 16 info

-- ─── Value-string tables ──────────────────────────────────────────────────────

-- Type identifiers (§5.4.1)  0=NULL(reserved) 1=HELLO 2=PASSWORD 3=CONNECT
-- Request and response share the same type byte; direction is shown via status
-- (0x00 = request, non-zero = response).
local MSG_TYPES = {
    [0x00] = "NULL (reserved)",
    [0x01] = "HELLO",
    [0x02] = "PASSWORD",
    [0x03] = "CONNECT",
}

-- Extension header identifiers (§5.4.2)
local HDR_IDS = {
    [0x00] = "NULL (reserved)",
    [0x01] = "Password",
    [0x02] = "New-Password",
    [0x03] = "Projector-Name",
    [0x04] = "IM-Type",
    [0x05] = "Projector-Command-Type",
}

-- Attribute values for Password / New-Password headers
local PASSWORD_ATTRS = {
    [0x00] = "NULL (no password)",
    [0x01] = "Plain",
}

-- Attribute values for the Projector-Name header
local NAME_ATTRS = {
    [0x00] = "NULL",
    [0x01] = "US-ASCII",
    [0x02] = "Shift-JIS (reserved)",
    [0x03] = "EUC-JP (reserved)",
}

-- Attribute values for the Projector-Command-Type header
local CMD_TYPE_ATTRS = {
    [0x16] = "ESC/VP Level6 (reserved)",
    [0x21] = "ESC/VP21 Ver1.0",
}

-- Status codes (§5.4.1)
-- 0x00 is used in request packets where status is not applicable.
local STATUS_CODES = {
    [0x00] = "Request",
    [0x20] = "OK",
    [0x40] = "Bad Request",
    [0x41] = "Unauthorized",
    [0x43] = "Forbidden",
    [0x45] = "Request not allowed",
    [0x53] = "Service Unavailable",
    [0x55] = "Protocol Version Not Supported",
}

-- ─── Protocol definition ──────────────────────────────────────────────────────

local escvpnet_proto = Proto("escvpnet", "ESC/VP.net Protocol")

-- ProtoFields: fixed 16-byte header
-- Offsets: 0-9 magic, 10 version, 11 type, 12-13 reserved, 14 status, 15 num_headers
local pf = {
    magic        = ProtoField.bytes ("escvpnet.magic",        "Magic"),
    version      = ProtoField.uint8 ("escvpnet.version",      "Version",     base.HEX),
    msg_type     = ProtoField.uint8 ("escvpnet.type",         "Type",        base.HEX, MSG_TYPES),
    reserved     = ProtoField.uint16("escvpnet.reserved",     "Reserved",    base.HEX),
    status       = ProtoField.uint8 ("escvpnet.status",       "Status",      base.HEX, STATUS_CODES),
    num_headers  = ProtoField.uint8 ("escvpnet.num_headers",  "Num Headers", base.DEC),

    -- Extension header subfields (one subtree per header, §5.4.2)
    ext_hdr      = ProtoField.bytes ("escvpnet.ext_hdr",          "Extension Header"),
    hdr_id       = ProtoField.uint8 ("escvpnet.hdr_id",           "Identifier",  base.DEC, HDR_IDS),
    hdr_attr     = ProtoField.uint8 ("escvpnet.hdr_attr",         "Attribute",   base.DEC),
    hdr_info     = ProtoField.bytes ("escvpnet.hdr_info",         "Information"),

    -- Post-handshake ESC/VP21 bidirectional data (TCP only)
    escvp21_data = ProtoField.string("escvpnet.escvp21_data", "ESC/VP21 Data"),
}

escvpnet_proto.fields = {
    pf.magic, pf.version, pf.msg_type, pf.reserved, pf.status, pf.num_headers,
    pf.ext_hdr, pf.hdr_id, pf.hdr_attr, pf.hdr_info,
    pf.escvp21_data,
}

-- ─── Expert info definitions ──────────────────────────────────────────────────

local ef = {
    -- Packet is shorter than the 16-byte header during handshake phase
    too_short = ProtoExpert.new(
        "escvpnet.too_short",
        "Packet too short for ESC/VP.net header (need 16 bytes)",
        expert.group.MALFORMED, expert.severity.ERROR),

    -- Version byte is not 0x10 as required by the specification
    bad_version = ProtoExpert.new(
        "escvpnet.bad_version",
        "Unexpected version byte (expected 0x10)",
        expert.group.PROTOCOL, expert.severity.WARN),

    -- Reserved field contains a non-zero value
    nonzero_reserved = ProtoExpert.new(
        "escvpnet.nonzero_reserved",
        "Reserved field is non-zero (expected 0x0000)",
        expert.group.PROTOCOL, expert.severity.NOTE),

    -- Payload length does not match num_headers × 18
    wrong_length = ProtoExpert.new(
        "escvpnet.wrong_length",
        "Payload length does not match num_headers \xc3\x97 18",
        expert.group.MALFORMED, expert.severity.WARN),
}

escvpnet_proto.experts = {
    ef.too_short, ef.bad_version, ef.nonzero_reserved, ef.wrong_length,
}

-- ─── Per-stream phase tracking ────────────────────────────────────────────────

-- Keyed by tostring(pinfo.conversation) → "handshake" | "data".
-- Only a TCP CONNECT response (type=0x03, status=0x20) triggers the transition
-- to "data".  UDP HELLO conversations never see a CONNECT response, so they
-- permanently remain in "handshake" phase.
local stream_phases = {}

-- ─── Extension header parser ────────────────────────────────────────────────────────────────

--- Parse `n` extension headers from `tvb` at byte `offset` into `tree`.
--- Each header is EXT_HDR_LEN (18) bytes: 1 id + 1 attr + 16 info.
local function parse_ext_headers(tvb, tree, offset, n)
    for i = 1, n do
        local hdr_start = offset + (i - 1) * EXT_HDR_LEN
        if hdr_start + EXT_HDR_LEN > tvb:len() then
            break  -- truncated; expert info was already added by caller
        end

        local id_val   = tvb(hdr_start,     1):uint()
        local attr_val = tvb(hdr_start + 1, 1):uint()
        local id_name  = HDR_IDS[id_val] or string.format("Unknown (0x%02X)", id_val)

        local hdr_item = tree:add(pf.ext_hdr, tvb(hdr_start, EXT_HDR_LEN))
        hdr_item:set_text(string.format("Extension Header %d: %s", i, id_name))

        hdr_item:add(pf.hdr_id, tvb(hdr_start, 1))

        local attr_item = hdr_item:add(pf.hdr_attr, tvb(hdr_start + 1, 1))
        local attr_label
        if     id_val == 0x01 or id_val == 0x02 then
            attr_label = PASSWORD_ATTRS[attr_val]
        elseif id_val == 0x03 then
            attr_label = NAME_ATTRS[attr_val]
        elseif id_val == 0x05 then
            attr_label = CMD_TYPE_ATTRS[attr_val]
        end
        if attr_label then
            attr_item:append_text("  [" .. attr_label .. "]")
        end

        -- Info field (16 bytes): bytes kept for packet-pane highlight.
        -- For text-bearing headers replace the label with the decoded string.
        local info_item = hdr_item:add(pf.hdr_info, tvb(hdr_start + 2, 16))
        if id_val == 0x01 or id_val == 0x02 or id_val == 0x03 then
            local decoded = tvb(hdr_start + 2, 16):string():match("^[^%z]*") or ""
            info_item:set_text('Information: "' .. decoded .. '"')
        end
    end
end

-- ─── Fixed header parser ────────────────────────────────────────────────────────────────

--- Parse the 16-byte ESC/VP.net fixed header into `tree`.
--- Returns (type_val, status_val, num_hdrs) on success.
--- Returns nil if magic does not match (not our protocol), or if the header is
--- truncated (expert info already added to `tree` in that case).
local function parse_header(tvb, pinfo, tree)
    -- Need at least MAGIC_LEN bytes to validate the magic prefix.
    if tvb:len() < MAGIC_LEN then
        return nil
    end

    -- Check for the "ESC/VP.net" magic string.
    if tvb(0, MAGIC_LEN):string() ~= MAGIC then
        return nil
    end

    -- Magic matched — add it to the subtree before any further length checks.
    tree:add(pf.magic, tvb(0, MAGIC_LEN))

    -- Full 16-byte header must be present.
    if tvb:len() < HEADER_LEN then
        tree:add_proto_expert_info(ef.too_short)
        return nil
    end

    -- Version (offset 10, 1 byte) — SHALL be 0x10.
    local ver_item = tree:add(pf.version, tvb(10, 1))
    local ver_val  = tvb(10, 1):uint()
    if ver_val ~= 0x10 then
        ver_item:add_proto_expert_info(ef.bad_version,
            string.format("Version is 0x%02X, expected 0x10", ver_val))
    end

    -- Type (offset 11, 1 byte) — decoded with MSG_TYPES value_string.
    tree:add(pf.msg_type, tvb(11, 1))
    local type_val = tvb(11, 1):uint()

    -- Reserved (offsets 12–13, 2 bytes) — SHALL be 0x0000.
    local res_item = tree:add(pf.reserved, tvb(12, 2))
    local res_val  = tvb(12, 2):uint()
    if res_val ~= 0x0000 then
        res_item:add_proto_expert_info(ef.nonzero_reserved,
            string.format("Reserved is 0x%04X, expected 0x0000", res_val))
    end

    -- Status (offset 14, 1 byte) — decoded with STATUS_CODES value_string.
    tree:add(pf.status, tvb(14, 1))
    local status_val = tvb(14, 1):uint()

    -- Num Headers (offset 15, 1 byte).
    tree:add(pf.num_headers, tvb(15, 1))
    local num_hdrs = tvb(15, 1):uint()

    return type_val, status_val, num_hdrs
end

-- ─── Main dissector function ──────────────────────────────────────────────────

function escvpnet_proto.dissector(tvb, pinfo, root)
    if tvb:len() == 0 then return 0 end

    pinfo.cols.protocol:set("ESC/VP.net")

    local conv_key = tostring(pinfo.conversation)
    local phase    = stream_phases[conv_key] or "handshake"

    -- ── Post-handshake: ESC/VP21 text stream ─────────────────────────────────
    -- After a successful CONNECT response the stream carries raw ESC/VP21
    -- text commands (ASCII, CR-terminated).  Display the payload as-is.
    if phase == "data" then
        -- If the magic is present this is a new handshake on a reused
        -- conversation key (Wireshark reuses conversations on TCP reconnect).
        -- Reset and fall through to handshake parsing.
        if tvb:len() >= MAGIC_LEN and tvb(0, MAGIC_LEN):string() == MAGIC then
            stream_phases[conv_key] = nil
            phase = "handshake"
        else
            local tree = root:add(escvpnet_proto, tvb(), "ESC/VP.net (ESC/VP21 data)")
            tree:add(pf.escvp21_data, tvb(0, tvb:len()))
            pinfo.cols.info:set("ESC/VP21 data")
            return tvb:len()
        end
    end

    -- ── Handshake phase: 16-byte binary header ────────────────────────────────
    local tree = root:add(escvpnet_proto, tvb(), "ESC/VP.net")
    local type_val, status_val, num_hdrs = parse_header(tvb, pinfo, tree)

    if type_val == nil then
        if tvb:len() < MAGIC_LEN or tvb(0, MAGIC_LEN):string() ~= MAGIC then
            pinfo.cols.info:set("[Unknown / non-ESC/VP.net data]")
        end
        return 0
    end

    -- Info column: "TYPE (request)" or "TYPE (response: STATUS_LABEL)"
    local type_name   = MSG_TYPES[type_val] or string.format("Unknown (0x%02X)", type_val)
    local status_name = STATUS_CODES[status_val]
    local direction
    if status_val == 0x00 then
        direction = "request"
    else
        direction = "response: " .. (status_name or string.format("0x%02X", status_val))
    end
    pinfo.cols.info:set(string.format("%s (%s)", type_name, direction))

    -- ── Extension headers (§5.4.2) ────────────────────────────────────────────
    if num_hdrs > 0 then
        local expected = HEADER_LEN + num_hdrs * EXT_HDR_LEN
        if tvb:len() < expected then
            tree:add_proto_expert_info(ef.wrong_length,
                string.format("Need %d bytes for %d extension header(s), have %d",
                              expected, num_hdrs, tvb:len()))
        end
        parse_ext_headers(tvb, tree, HEADER_LEN, num_hdrs)
    end

    -- ── Phase transition ──────────────────────────────────────────────────────
    -- CONNECT response (type=0x03, status=0x20) → subsequent TCP bytes are
    -- ESC/VP21 ASCII commands.  UDP HELLO conversations never trigger this.
    if type_val == 0x03 and status_val == 0x20 then
        stream_phases[conv_key] = "data"
    end

    return tvb:len()
end

-- ─── Register on TCP port 3629 (session) and UDP port 3629 (HELLO) ───────────
-- TCP: full session mode — PASSWORD / CONNECT handshake then ESC/VP21 pipe
-- UDP: session-less HELLO discovery (broadcast to 255.255.255.255)
DissectorTable.get("tcp.port"):add(ESCVPNET_PORT, escvpnet_proto)
DissectorTable.get("udp.port"):add(ESCVPNET_PORT, escvpnet_proto)
