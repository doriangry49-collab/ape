# SPEC-0003: Configuration

## Goal

Define how APE stores and exposes workspace configuration.

## Requirements

- Use `.ape/config.toml` as the workspace configuration file.
- Provide a `config` command to inspect the current workspace configuration.
- Support locating configuration from the current directory or parent directories.

## Non-Goals

- Introducing a new configuration format.
- Adding external configuration services or dependencies.

## Implementation Notes

Configuration should remain simple and local to the workspace. The command should report the workspace path and config location clearly without changing established CLI behavior.

## Tests

- Verify configuration is created and read correctly.
- Ensure the `config` command reports the expected workspace state.

## Acceptance Criteria

- `.ape/config.toml` is created and used as the workspace configuration file.
- The `config` command reports the workspace state successfully.
- The behavior remains simple and backward compatible.
