# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from types import CodeType, FrameType, FunctionType, MethodType, ModuleType
from typing import TYPE_CHECKING, Any, Literal

from .types import IdentifierType
from .util import call_in_frame, get_line_numbers, get_source_hash, getrealsourcelines

if TYPE_CHECKING:  # pragma: no cover
    from .callback import Callback
    from .handler import EventHandler


DISABLE = sys.monitoring.DISABLE


class _Event:
    def __init__(
        self,
        code: CodeType | None,
        event_type: Literal["line", "start", "return"],
        event_data: dict | None,
    ):
        self.code = code
        self.event_type = event_type
        self.event_data = event_data or {}


class Trigger:
    def __init__(
        self,
        events: list[_Event],
        condition: str | Callable[..., bool] | None = None,
        is_global: bool = False,
    ):
        self.events = events
        self.condition = condition
        self.is_global = is_global

    @classmethod
    def _get_code_from_entity(
        cls, entity: CodeType | FunctionType | MethodType | ModuleType | type | None
    ) -> list[CodeType] | list[None]:
        """
        Get code objects from the given entity.
        """
        code_objects: list[CodeType] = []

        entity_list = []

        if entity is None:
            return [None]

        if inspect.ismodule(entity) or inspect.isclass(entity):
            for _, obj in inspect.getmembers_static(
                entity, lambda o: isinstance(o, (FunctionType, MethodType, CodeType))
            ):
                entity_list.append(obj)
        else:
            entity_list.append(entity)

        for entity in entity_list:
            if inspect.isfunction(entity) or inspect.ismethod(entity):
                entity = inspect.unwrap(entity)
                if inspect.isfunction(entity) or inspect.ismethod(entity):
                    code_objects.append(entity.__code__)
                else:  # pragma: no cover
                    raise TypeError(
                        f"Expected a function or method, got {type(entity)}"
                    )
            elif inspect.iscode(entity):
                code_objects.append(entity)
            else:
                raise TypeError(f"Unknown entity type: {type(entity)}")

        return code_objects

    @classmethod
    def unify_identifiers(
        cls,
        entity: CodeType | FunctionType | MethodType | ModuleType | type | None,
        *identifiers: IdentifierType | tuple[IdentifierType, ...],
    ) -> tuple[IdentifierType | tuple[IdentifierType, ...], ...]:
        """Unify identifiers by resolving relative line numbers."""

        def unify_identifier(
            entity: CodeType | FunctionType | MethodType | ModuleType | type | None,
            identifier: IdentifierType,
        ) -> IdentifierType:
            if (
                isinstance(identifier, str)
                and identifier.startswith("+")
                and identifier[1:].isdigit()
            ):
                if entity is None:
                    raise ValueError(
                        "Cannot use relative line numbers with a None entity."
                    )
                elif isinstance(entity, ModuleType):
                    return int(identifier)
                else:
                    _, start_line = getrealsourcelines(entity)
                    return start_line + int(identifier)
            return identifier

        unified_identifiers: list[IdentifierType | tuple[IdentifierType, ...]] = []
        for identifier in identifiers:
            if isinstance(identifier, tuple):
                unified_identifiers.append(
                    tuple(unify_identifier(entity, ident) for ident in identifier)
                )
            else:
                unified_identifiers.append(unify_identifier(entity, identifier))

        return tuple(unified_identifiers)

    @classmethod
    def when(
        cls,
        entity: CodeType | FunctionType | MethodType | ModuleType | type | None,
        *identifiers: IdentifierType | tuple[IdentifierType, ...],
        condition: str | Callable[..., bool | Any] | None = None,
        source_hash: str | None = None,
    ):
        if isinstance(condition, str):
            try:
                compile(condition, "<string>", "eval")
            except SyntaxError:
                raise ValueError(f"Invalid condition expression: {condition}")
        elif condition is not None and not callable(condition):
            raise TypeError(
                f"Condition must be a string or callable, got {type(condition)}"
            )

        if source_hash is not None:
            if not isinstance(source_hash, str):
                raise TypeError(
                    f"source_hash must be a string, got {type(source_hash)}"
                )
            if entity is None:
                raise ValueError("source_hash cannot be used with a None entity.")
            if get_source_hash(entity) != source_hash:
                raise ValueError(
                    "The source hash does not match the entity's source code."
                )

        events = []

        code_objects = cls._get_code_from_entity(entity)

        if not identifiers:
            for code in code_objects:
                events.append(_Event(code, "line", {"line_number": None}))
        else:
            identifiers = cls.unify_identifiers(entity, *identifiers)
            for identifier in identifiers:
                if identifier == "<start>":
                    for code in code_objects:
                        events.append(_Event(code, "start", None))
                elif identifier == "<return>":
                    for code in code_objects:
                        events.append(_Event(code, "return", None))
                else:
                    for code in code_objects:
                        if code is None:
                            # Global event, entity is None
                            events.append(
                                _Event(
                                    None,
                                    "line",
                                    {"line_number": None, "identifier": identifier},
                                )
                            )
                        else:
                            line_numbers = get_line_numbers(code, identifier)
                            for c, numbers in line_numbers.items():
                                for number in numbers:
                                    events.append(
                                        _Event(c, "line", {"line_number": number})
                                    )

        if not events:
            raise ValueError(
                "Could not set any event based on the entity and identifiers."
            )

        return cls(events, condition=condition, is_global=entity is None)

    def bp(self) -> "EventHandler":
        from .callback import Callback

        return self._submit_callback(Callback.bp())

    def do(self, func: str | Callable) -> "EventHandler":
        from .callback import Callback

        return self._submit_callback(Callback.do(func))

    def goto(self, target: str | int) -> "EventHandler":
        from .callback import Callback

        return self._submit_callback(Callback.goto(target))

    def has_event(self, frame: FrameType) -> bool | Any:
        if self.is_global and self.events[0].event_type == "line":
            identifier = self.events[0].event_data.get("identifier")
            assert isinstance(identifier, (str, int, tuple))
            line_numbers = get_line_numbers(frame.f_code, identifier).get(
                frame.f_code, None
            )
            if line_numbers is None:
                return False
            elif frame.f_lineno not in line_numbers:
                return False
        return True

    def should_fire(self, frame: FrameType) -> bool | Any:
        if self.condition is None:
            return True
        try:
            if isinstance(self.condition, str):
                return eval(self.condition, frame.f_globals, frame.f_locals)
            elif callable(self.condition):
                return call_in_frame(self.condition, frame)
        except Exception:
            return False

        assert False, "Unknown condition type"  # pragma: no cover

    def _submit_callback(self, callback: "Callback") -> "EventHandler":
        from .handler import EventHandler

        handler = EventHandler(self, callback)
        handler.submit()

        return handler


when = Trigger.when
