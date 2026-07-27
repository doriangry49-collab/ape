# SPEC-0004: Workspace

## Goal

Describe the shared workspace discovery behavior used by the CLI.

## Requirements

- Provide a reusable `workspace.py` module.
- Support workspace discovery from the current directory and parent directories.
- Enable shared workspace helper logic for CLI commands.
- Preserve the existing command behavior and output.

## Non-Goals

- Changing the CLI command names or output format.
- Adding new dependencies for workspace discovery.

## Implementation Notes

Workspace discovery should be centralized in a simple helper so the logic can be reused consistently. The behavior should remain minimal and focused on locating `.ape/config.toml`.

## Tests

- Verify discovery succeeds for the current directory.
- Verify discovery succeeds for child and parent directories.
- Verify CLI behavior remains unchanged.

## Acceptance Criteria

- Workspace discovery is implemented in `src/ape/workspace.py`.
- Parent directory discovery works as expected.
- Existing CLI commands continue to function without behavior changes.
