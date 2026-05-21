## MODIFIED Requirements

### Requirement: Display recent command log
The TUI SHALL display a scrollable log of the most recent ESC/VP21 commands received (across all transports) with timestamps formatted as `HH:MM:SS.mmm` and the transport they arrived on.

#### Scenario: Command logged on receipt
- **WHEN** any transport receives a command
- **THEN** the command, transport name, and millisecond-precision timestamp appear in the log

#### Scenario: Closely spaced commands remain distinguishable
- **WHEN** multiple commands are received within the same second
- **THEN** their log entries preserve millisecond precision so operators can distinguish the event order within that second