"""
zimbro/test_context.py — Isolated test runtime for Zimbro causal tests.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CausalEvent:
    kind: str
    entity: str = ""
    field: str = ""
    value: Any = None
    timestamp: float = dc_field(default_factory=time.time)
    metadata: Dict[str, Any] = dc_field(default_factory=dict)


class ZimbroTestContext:
    """Per-test isolated context with entity snapshots and causal timeline."""

    ENTITY_NAMES = (
        "Order", "Payment", "Fulfillment", "Invoice", "Customer", "Product"
    )

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.events: List[CausalEvent] = []
        self.mocks: Dict[str, Dict[str, Any]] = {}
        self._saved_variables: Dict[str, Any] = {}
        self._variable_snapshot: Optional[Dict[str, Any]] = None

    def begin(self):
        self._variable_snapshot = dict(self.interpreter.variables)
        self.events.clear()
        self.mocks.clear()
        self.reset_entity_storage()

    def end(self):
        if self._variable_snapshot is not None:
            self.interpreter.variables = dict(self._variable_snapshot)
        self._variable_snapshot = None

    def reset_entity_storage(self):
        for name in self.ENTITY_NAMES:
            cls = self.interpreter.variables.get(name)
            if cls is not None and hasattr(cls, "_absinto_storage"):
                cls._absinto_storage = []

    def register_mock(self, target: str, config: Optional[Dict[str, Any]] = None):
        self.mocks[target] = config or {"active": True}

    def clear_mocks(self):
        self.mocks.clear()

    def record_event(self, kind: str, entity: str = "", field: str = "", value: Any = None, **metadata):
        self.events.append(
            CausalEvent(kind=kind, entity=entity, field=field, value=value, metadata=metadata)
        )

    def observe_assignment(self, target_name: str, value: Any):
        if "." in target_name:
            entity, field = target_name.split(".", 1)
            self.record_event("set", entity=entity, field=field, value=value)

    def observe_instance(self, instance: Any):
        entity_name = getattr(instance, "__entity_name__", None) or type(instance).__name__
        for field_name in getattr(instance, "__fields__", {}):
            try:
                value = getattr(instance, field_name)
            except Exception:
                continue
            self.record_event("state", entity=entity_name, field=field_name, value=value, instance=id(instance))

    def observe_call(self, target: str, result: Any = None):
        self.record_event("call", entity=target, value=result)

    def verify_causal(
        self,
        operator: str,
        subject: str,
        obj: str,
        subject_expr: str = "",
        object_expr: str = "",
        modifiers: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        modifiers = modifiers or {}
        subject_text = subject_expr or subject
        object_text = object_expr or obj

        if operator == "causes":
            return self._verify_causes(subject_text, object_text, modifiers)
        if operator == "prevents":
            return self._verify_prevents(subject_text, object_text, modifiers)
        if operator == "requires":
            return self._verify_requires(subject_text, object_text, modifiers)
        if operator == "precedes":
            return self._verify_precedes(subject_text, object_text, modifiers)
        if operator == "never":
            return self._verify_never(subject_text, object_text, modifiers)

        return False, f"Unknown causal operator: {operator}"

    def _verify_causes(self, subject: str, obj: str, modifiers: Dict[str, Any]) -> Tuple[bool, str]:
        if not self._preconditions_met(modifiers):
            return False, f"Precondition not met: {modifiers}"

        subj_ok, subj_msg = self._expression_holds(subject, expect_true=True)
        if not subj_ok:
            return False, f"Cause not established ({subject}): {subj_msg}"

        obj_ok, obj_msg = self._expression_holds(obj, expect_true=True)
        if not obj_ok:
            return False, f"Effect not observed ({obj}): {obj_msg}"

        if not self._timeline_respects(subject, obj, after=True):
            return False, f"Effect {obj} did not follow cause {subject}"

        return True, ""

    def _verify_prevents(self, subject: str, obj: str, modifiers: Dict[str, Any]) -> Tuple[bool, str]:
        if not self._preconditions_met(modifiers):
            return False, f"Precondition not met: {modifiers}"

        subj_ok, _ = self._expression_holds(subject, expect_true=True)
        if not subj_ok:
            return False, f"Preventing condition not active: {subject}"

        obj_ok, _ = self._expression_holds(obj, expect_true=True)
        if obj_ok:
            return False, f"Effect should have been prevented but holds: {obj}"

        return True, ""

    def _verify_requires(self, subject: str, obj: str, modifiers: Dict[str, Any]) -> Tuple[bool, str]:
        obj_ok, obj_msg = self._expression_holds(obj, expect_true=True)
        if not obj_ok:
            return False, f"Required effect missing ({obj}): {obj_msg}"

        subj_ok, subj_msg = self._expression_holds(subject, expect_true=True)
        if not subj_ok:
            return False, f"Requirement not satisfied ({subject}): {subj_msg}"

        return True, ""

    def _verify_precedes(self, subject: str, obj: str, modifiers: Dict[str, Any]) -> Tuple[bool, str]:
        subj_ok, subj_msg = self._expression_holds(subject, expect_true=True)
        obj_ok, obj_msg = self._expression_holds(obj, expect_true=True)
        if not subj_ok:
            return False, f"Preceding event missing ({subject}): {subj_msg}"
        if not obj_ok:
            return False, f"Following event missing ({obj}): {obj_msg}"
        if not self._timeline_respects(subject, obj, after=True):
            return False, f"{subject} must precede {obj}"
        return True, ""

    def _verify_never(self, subject: str, obj: str, modifiers: Dict[str, Any]) -> Tuple[bool, str]:
        # never A before B  →  A must not hold while B has not been established
        a_ok, _ = self._expression_holds(subject, expect_true=True)
        b_ok, _ = self._expression_holds(obj, expect_true=True)
        if a_ok and not b_ok:
            return False, f"{subject} occurred before {obj}"
        if subject and not obj:
            if a_ok:
                return False, f"Forbidden condition occurred: {subject}"
        return True, ""

    def _preconditions_met(self, modifiers: Dict[str, Any]) -> bool:
        given = modifiers.get("given")
        if not given:
            return True
        ok, _ = self._expression_holds(str(given), expect_true=True)
        return ok

    def _timeline_respects(self, subject: str, obj: str, after: bool = True) -> bool:
        subj_time = self._latest_match_time(subject)
        obj_time = self._latest_match_time(obj)
        if subj_time is None or obj_time is None:
            return True
        return obj_time >= subj_time if after else obj_time < subj_time

    def _latest_match_time(self, expr: str) -> Optional[float]:
        parsed = self._parse_expression(expr)
        if not parsed:
            return None
        entity, field, op, expected = parsed
        latest = None
        for event in self.events:
            if event.entity == entity and (not field or event.field == field):
                if field and op and not self._compare(event.value, op, expected):
                    continue
                latest = event.timestamp
        return latest

    def _expression_holds(self, expr: str, expect_true: bool = True) -> Tuple[bool, str]:
        expr = (expr or "").strip()
        if not expr:
            return not expect_true, "empty expression"

        if "." in expr and not any(op in expr for op in ("==", "!=", ">", "<", ">=", "<=")):
            entity, action = expr.split(".", 1)
            return self._check_action(entity.strip(), action.strip())

        parsed = self._parse_expression(expr)
        if parsed:
            entity, field, op, expected = parsed
            return self._check_entity_state(entity, field, op, expected)

        return False, f"Unable to evaluate causal expression: {expr}"

    def _parse_expression(self, expr: str) -> Optional[Tuple[str, str, str, Any]]:
        expr = expr.strip()
        patterns = [
            r"^(\w+)\.(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, expr)
            if not match:
                continue
            groups = match.groups()
            entity = groups[0]
            field = groups[1]
            op = groups[2]
            raw = groups[3].strip().strip('"').strip("'")
            if raw in ("true", "True"):
                expected: Any = True
            elif raw in ("false", "False"):
                expected = False
            else:
                try:
                    expected = float(raw) if "." in raw else int(raw)
                except ValueError:
                    expected = raw
            return entity, field, op, expected
        return None

    def _check_entity_state(self, entity: str, field: str, op: str, expected: Any) -> Tuple[bool, str]:
        instances = self._collect_instances(entity)
        if not instances:
            if op == "!=" and expected is None:
                return True, ""
            return False, f"No instances of {entity}"

        for instance in instances:
            try:
                actual = getattr(instance, field)
            except Exception:
                continue
            if self._compare(actual, op, expected):
                return True, ""

        return False, f"No {entity} with {field} {op} {expected}"

    def _check_action(self, entity: str, action: str) -> Tuple[bool, str]:
        mock_key = entity if entity in self.mocks else f"{entity}.{action}"
        if mock_key in self.mocks and self.mocks[mock_key].get("active", True):
            return True, ""
        if entity in self.mocks and self.mocks[entity].get("active", True):
            return True, ""

        action_state_map = {
            "created": ("id", ">", 0),
            "refunded": ("status", "==", "refunded"),
            "confirmed": ("status", "==", "confirmed"),
            "cancelled": ("status", "==", "cancelled"),
            "generated": ("status", "==", "generated"),
            "delivered": ("status", "==", "delivered"),
            "shipped": ("status", "==", "shipped"),
            "failed": ("status", "==", "failed"),
            "authenticated": ("status", "==", "active"),
            "processed": ("status", "==", "confirmed"),
            "started": ("status", "==", "pending"),
            "persisted": ("id", ">", 0),
            "loaded": ("id", ">", 0),
            "login": ("status", "==", "active"),
            "save": ("id", ">", 0),
            "GET": ("id", ">", 0),
        }

        if action in action_state_map:
            field, op, expected = action_state_map[action]
            if expected is None:
                if self._collect_instances(entity):
                    return True, ""
                return False, f"No instances of {entity}"
            return self._check_entity_state(entity, field, op, expected)

        instances = self._collect_instances(entity)
        if action in ("created", "loaded", "persisted", "processed", "started") and instances:
            return True, ""

        for event in self.events:
            if event.entity == entity and action in (event.kind, str(event.metadata.get("action", ""))):
                return True, ""

        return False, f"Action {entity}.{action} not observed"

    def _collect_instances(self, entity_name: str) -> List[Any]:
        found: List[Any] = []
        cls = self.interpreter.variables.get(entity_name)
        if cls is not None and hasattr(cls, "all"):
            try:
                found.extend(cls.all())
            except Exception:
                pass
        for value in self.interpreter.variables.values():
            if hasattr(value, "__entity_name__") and value.__entity_name__ == entity_name:
                if value not in found:
                    found.append(value)
            elif type(value).__name__ == entity_name and hasattr(value, "__fields__"):
                if value not in found:
                    found.append(value)
        return found

    @staticmethod
    def _compare(actual: Any, op: str, expected: Any) -> bool:
        if op == "==":
            return actual == expected
        if op == "!=":
            return actual != expected
        if op == ">":
            return actual > expected
        if op == "<":
            return actual < expected
        if op == ">=":
            return actual >= expected
        if op == "<=":
            return actual <= expected
        return False
