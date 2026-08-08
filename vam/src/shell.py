"""Conservative executable lowering for finite Core ``shell(...)`` relations."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Protocol

from src.core.language import VeyraExpr, infer_veyra, normal_text

from .compiler import SUPPORTED_OBSERVERS, VamCompileError

logger = logging.getLogger(__name__)
NON_CERTIFICATE_BOUNDARY = "finite shell conjunction carrier only; no VAM certificate claim"


class ShellCompiler(Protocol):
    """Narrow compiler surface used by the shell lowering hook."""

    def emit(self, op: str, *args: object) -> str: ...

    def compile(self, expr: VeyraExpr) -> str: ...


@dataclass(frozen=True)
class ShellLoweringRow:
    """Audit row for one shell child relation."""

    source: str
    status: str
    register: str
    obstruction_register: str | None = None


@dataclass(frozen=True)
class ShellCarrier:
    """Minimal finite conjunction carrier encoded as a deterministic ``REZ`` label."""

    source: str
    rows: tuple[ShellLoweringRow, ...]
    boundary: str = NON_CERTIFICATE_BOUNDARY
    certificate_claim: str | None = None

    @property
    def status(self) -> str:
        """Deterministic carrier status from child rows and certificate boundary."""
        return "transported" if self.transported else "blocked"

    @property
    def transported(self) -> bool:
        """True when every child row transported and no certificate claim exists."""
        return _all_transport_rows(self.rows, self.certificate_claim)

    def label(self) -> str:
        """Return stable string payload suitable for current VAM string-only IR."""
        logger.debug("shell carrier label entry source=%s rows=%d", self.source, len(self.rows))
        payload = {
            "boundary": self.boundary,
            "certificate_claim": self.certificate_claim,
            "child_count": len(self.rows),
            "obstruction_registers": tuple(row.obstruction_register for row in self.rows if row.obstruction_register),
            "rows": tuple(
                {
                    "obstruction_register": row.obstruction_register,
                    "register": row.register,
                    "source": row.source,
                    "status": row.status,
                }
                for row in self.rows
            ),
            "source": self.source,
            "status": self.status,
            "transported": self.transported,
        }
        result = "shell-carrier:" + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        logger.debug("shell carrier label exit chars=%d", len(result))
        return result


def decode_shell_carrier_label(label: str) -> dict[str, object]:
    """Decode a shell carrier label for tests and diagnostics."""
    logger.debug("decode shell carrier entry chars=%d", len(label))
    prefix = "shell-carrier:"
    if not label.startswith(prefix):
        logger.error("decode shell carrier bad prefix label=%s", label)
        raise ValueError("not a shell carrier label")
    result = json.loads(label[len(prefix) :])
    logger.debug("decode shell carrier exit status=%s", result.get("status"))
    return result


def lower_shell(compiler: ShellCompiler, expr: VeyraExpr) -> str:
    """Lower a finite shell to executable child rows plus honest carrier status.

    A currently supported shell is a non-empty finite list of directly executable
    ``echo`` child relations whose observers are already in VAM's finite observer
    subset.  Passing shells return a deterministic finite conjunction carrier
    over the child ``Echo`` rows, not certificate evidence.

    Blocked or unsupported children still execute as explicit ``OBSTRUCT`` rows
    instead of being silently treated as proof evidence.
    """
    logger.debug("lower_shell entry children=%d", len(expr.args))
    if expr.head != "shell" or not expr.args:
        logger.error("lower_shell malformed expr=%s", normal_text(expr))
        raise VamCompileError(f"unsupported shell form: {normal_text(expr)}")

    rows: list[ShellLoweringRow] = []
    for child in expr.args:
        row = _lower_child(compiler, child)
        rows.append(row)

    carrier = ShellCarrier(normal_text(expr), tuple(rows))
    result = compiler.emit("REZ", carrier.label())
    logger.debug("lower_shell exit rows=%d root=%s", len(rows), result)
    return result


def _all_transport_rows(rows: tuple[ShellLoweringRow, ...], certificate_claim: str | None) -> bool:
    logger.debug("all transport rows entry rows=%d claim=%s", len(rows), certificate_claim)
    result = certificate_claim is None and all(
        row.status == "transported" and row.obstruction_register is None for row in rows
    )
    logger.debug("all transport rows exit result=%s", result)
    return result


def _lower_child(compiler: ShellCompiler, child: VeyraExpr) -> ShellLoweringRow:
    source = normal_text(child)
    logger.debug("lower_shell child entry source=%s", source)
    if not _is_supported_echo(child):
        marker = compiler.emit("REZ", source)
        obstruction = compiler.emit("OBSTRUCT", "shell.unsupported_child", marker)
        return ShellLoweringRow(source, "unsupported", marker, obstruction)

    check = infer_veyra(child)
    if check.status == "unknown":
        marker = compiler.emit("REZ", source)
        obstruction = compiler.emit("OBSTRUCT", f"shell.unknown:{check.obstruction}", marker)
        return ShellLoweringRow(source, "unknown", marker, obstruction)

    try:
        relation = compiler.compile(child)
    except VamCompileError as exc:
        marker = compiler.emit("REZ", source)
        obstruction = compiler.emit("OBSTRUCT", f"shell.lowering_error:{exc}", marker)
        return ShellLoweringRow(source, "unsupported", marker, obstruction)

    if check.status == "blocked" or not check.ok:
        obstruction = compiler.emit("OBSTRUCT", f"shell.blocked:{check.obstruction}", relation)
        return ShellLoweringRow(source, "blocked", relation, obstruction)
    return ShellLoweringRow(source, "transported", relation, None)


def _is_supported_echo(expr: VeyraExpr) -> bool:
    if expr.head != "echo" or len(expr.args) != 3:
        return False
    observer = expr.args[2]
    if observer.head != "observer" or observer.args:
        return False
    label = observer.label if observer.label is not None else "kind"
    return label in SUPPORTED_OBSERVERS
