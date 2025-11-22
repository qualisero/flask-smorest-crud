from typing import Type
import marshmallow as ma
from sqlalchemy.orm import DeclarativeBase


def generate_filter_schema(base_schema):

    temp_instance = base_schema()

    new_declared_fields = {}
    remove_declared_fields = set()
    for field_name, field_obj in temp_instance.fields.items():
        if isinstance(field_obj, ma.fields.DateTime) or isinstance(field_obj, ma.fields.Date):
            # Replace date fields with range fields
            field_type = type(field_obj)
            new_declared_fields[f"{field_name}__from"] = field_type(
                load_default=None, load_only=True, dump_only=False, required=False
            )
            new_declared_fields[f"{field_name}__to"] = field_type(
                load_default=None, load_only=True, dump_only=False, required=False
            )
            remove_declared_fields |= {field_name}
        if (
            isinstance(field_obj, ma.fields.Integer)
            or isinstance(field_obj, ma.fields.Float)
            or isinstance(field_obj, ma.fields.Decimal)
        ):
            # Add min/max fields for numeric types
            field_type = type(field_obj)
            new_declared_fields[f"{field_name}__min"] = field_type(
                load_default=None, load_only=True, dump_only=False, required=False
            )
            new_declared_fields[f"{field_name}__max"] = field_type(
                load_default=None, load_only=True, dump_only=False, required=False
            )
            if not isinstance(field_obj, ma.fields.Integer):
                # Equality filters on float/decimal fields don't make much sense
                remove_declared_fields |= {field_name}
        if isinstance(field_obj, ma.fields.Enum):
            # Add __in filter for enum fields
            new_declared_fields[f"{field_name}__in"] = ma.fields.List(
                ma.fields.Enum(field_obj.enum), load_default=None, load_only=True, dump_only=False, required=False
            )

    class FilterSchema(base_schema):

        def on_bind_field(self, field_name, field_obj):
            # Called automatically when a field is attached to this schema
            field_obj.load_default = None
            field_obj.load_only = True
            field_obj.dump_only = False
            field_obj.required = False

        @ma.post_load
        def remove_none_fields(self, data, **kwargs):
            # Remove fields with None values from the deserialized data
            return {k: v for k, v in data.items() if v is not None}

        class Meta(base_schema.Meta):
            partial = True
            load_instance = False
            # NOTE: need to also set this in bp.arguments() call for flask-smorest to work:
            unknown = ma.RAISE

    # Add the new fields to the class's declared_fields
    for field_name, field_obj in new_declared_fields.items():
        setattr(FilterSchema, field_name, field_obj)
        FilterSchema._declared_fields[field_name] = field_obj
    # Remove fields that have been replaced with range fields
    for field_name in remove_declared_fields:
        if field_name in FilterSchema._declared_fields:
            del FilterSchema._declared_fields[field_name]

    return FilterSchema


def get_statements_from_filters(kwargs: dict, model: Type[DeclarativeBase]) -> set:
    """Convert query kwargs into SQLAlchemy filters based on the schema."""
    filters = set()

    for field_name, value in kwargs.items():
        if value is None:
            continue
        if field_name.endswith("__from"):
            base_field = getattr(model, field_name[:-6])
            filters |= {base_field >= value}
        elif field_name.endswith("__to"):
            base_field = getattr(model, field_name[:-4])
            filters |= {base_field <= value}
        elif field_name.endswith("__min"):
            base_field = getattr(model, field_name[:-5])
            filters |= {base_field >= value}
        elif field_name.endswith("__max"):
            base_field = getattr(model, field_name[:-5])
            filters |= {base_field <= value}
        else:
            filters |= {getattr(model, field_name) == value}

    return filters
