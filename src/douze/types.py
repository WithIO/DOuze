from collections import ChainMap
from dataclasses import Field, fields, is_dataclass
from typing import Any, Text, Union, get_type_hints

# noinspection PyPep8Naming
from uuid import UUID as BaseUuid

from typefit.compat import get_args, get_origin
from typefit.meta import Source
from typefit.serialize import SaneSerializer


class Uuid(BaseUuid):
    def __new__(cls, uuid: Text) -> "Uuid":
        self = super().__new__(cls)
        # noinspection PyTypeChecker
        cls.__init__(self, uuid)
        return self

    def __typefit_serialize__(self):
        return f"{self}"


def is_optional(field_type):
    """
    Checks fields that should be removed from output JSON if null, aka the
    fields that are mapped to a dataclass or a NamedTuple and which are
    optional. If they are None, we consider they shouldn't be in the output.
    """

    if not (get_origin(field_type) is Union):
        return False

    found_none = False
    found_dataclass = False

    for arg in get_args(field_type):
        if arg is not None and arg is not None.__class__:
            found_none = True
        elif is_dataclass(arg):
            found_dataclass = True
        elif issubclass(arg, tuple) and hasattr(arg, "_fields"):
            found_dataclass = True

    return found_dataclass and found_none


class UndefinedSerializer(SaneSerializer):
    """
    Removes from the output JSON the optional fields if they are not
    specified.

    See Also
    --------
    is_optional
    """

    def serialize_dataclass(self, obj: Any):
        """
        Same as parent but twisted a little bit. The "optionality test" happens
        before reverse source mapping is done, that's maybe not what you
        expected.
        """

        def _get_values():
            field: Field
            for field in fields(obj.__class__):
                if is_optional(field.type) and getattr(obj, field.name) is None:
                    continue

                if field.metadata and "typefit_source" in field.metadata:
                    source: Source = field.metadata["typefit_source"]
                    yield {
                        k: self.serialize(v)
                        for k, v in source.value_to_json(field.name, obj).items()
                    }
                else:
                    yield {field.name: self.serialize(getattr(obj, field.name))}

        return dict(ChainMap(*_get_values()))

    def serialize_tuple(self, obj: tuple):
        """
        Same as parent but with an additional check to test if the field is
        optional.
        """

        return {
            k: self.serialize(getattr(obj, k))
            for k, field_type in get_type_hints(obj.__class__).items()
            if not (is_optional(field_type) and getattr(obj, k) is None)
        }
