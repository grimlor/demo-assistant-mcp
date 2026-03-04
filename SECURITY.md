# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly by emailing the maintainer directly rather than opening a public
issue.

## Scope

This project is an MCP server that orchestrates demo script execution with
Copilot. Security considerations include:

- **Demo script files** — Demo definitions may contain sensitive project
  context or internal process details. Review before sharing publicly.
- **Demo state** — Demo state (step outputs, variables) is held in memory
  only and not persisted to disk.
- **MCP transport** — The server communicates over stdio by default. Ensure
  your MCP client configuration does not expose the transport to untrusted
  processes.

## Best Practices

- Don't commit demo scripts containing secrets or internal URLs
- Review demo variable outputs before logging or sharing
- Keep your MCP client configuration secure
- Don't expose the MCP server to untrusted network access
