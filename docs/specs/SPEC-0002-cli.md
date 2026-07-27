# SPEC-0002: CLI

## Goal

Describe the core CLI surface for the initial APE release.

## Requirements

- Provide a `doctor` command for environment inspection.
- Provide a `version` command for package version reporting.
- Provide an `init` command to create a minimal workspace structure.
- Keep the command names and behavior stable.

## Non-Goals

- Adding new commands beyond the current CLI surface.
- Rewriting the command structure in a breaking way.

## Implementation Notes

The CLI should remain simple and consistent with the existing command set. New functionality should be additive and preserve the current user experience.

## Tests

- Verify each CLI command returns the expected output and exit status.
- Preserve backward compatibility for existing command behavior.

## Acceptance Criteria

- The `doctor`, `version`, and `init` commands work as documented.
- Existing command behavior remains intact for current users.
- The CLI remains straightforward to understand and maintain.
