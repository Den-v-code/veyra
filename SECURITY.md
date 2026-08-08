# Security Policy

## Supported versions

Security fixes are developed for the current public release line. Older
releases may receive fixes when practical, but no long-term support schedule is
currently promised.

## Reporting a vulnerability

Please report vulnerabilities through the repository host's private security
reporting feature. If that feature is unavailable, contact the maintainers
through a private address published with the repository before sharing exploit
details.

Do not include secrets, personal information, private infrastructure details,
or a working exploit in a public issue.

A useful report includes:

- affected release or commit;
- affected component and entry point;
- reproduction steps or a minimal reproducer;
- expected and observed behavior;
- practical impact and required preconditions;
- suggested mitigation, if known.

Maintainers will acknowledge reports when possible, investigate, coordinate a
fix, and credit reporters who request attribution. Response times are best
effort; this research project does not currently offer a service-level
guarantee.

## Scope

Security issues include unsafe parsing, resource-exhaustion bypasses, path or
process boundary failures, untrusted-code execution, dependency compromise,
credential exposure, and incorrect fail-open behavior.

Mathematical errors, unsupported generalizations, and proof-boundary mistakes
are also important, but they may be reported as ordinary correctness issues
unless they create a concrete security impact. When uncertain, use the private
channel.

## Disclosure

Please allow reasonable time for diagnosis and a release before public
disclosure. Once a fix is available, the project may publish an advisory that
describes the affected versions, impact, and remediation without exposing
unnecessary sensitive detail.
