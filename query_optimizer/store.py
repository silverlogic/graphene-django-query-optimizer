from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.db.models import Expression, Model, Prefetch, QuerySet
from django.db.models.constants import LOOKUP_SEP
from graphene_django.registry import get_global_registry

from .settings import optimizer_settings
from .utils import mark_optimized

if TYPE_CHECKING:
    from .types import DjangoObjectType
    from .typing import PK, GQLInfo, Optional, TypeVar

    TModel = TypeVar("TModel", bound=Model)


__all__ = [
    "QueryOptimizerStore",
]


@dataclass
class CompilationResults:
    only_fields: list[str] = field(default_factory=list)
    select_related: list[str] = field(default_factory=list)
    prefetch_related: list[Prefetch] = field(default_factory=list)


class QueryOptimizerStore:
    """Store for holding optimization data."""

    def __init__(self, model: type[Model], info: GQLInfo) -> None:
        self.model = model
        self.info = info
        self.only_fields: list[str] = []
        self.related_fields: list[str] = []
        self.annotations: dict[str, Expression] = {}
        self.select_stores: dict[str, QueryOptimizerStore] = {}
        self.prefetch_stores: dict[str, QueryOptimizerStore] = {}

    def optimize_queryset(self, queryset: QuerySet[TModel], *, pk: PK = None) -> QuerySet[TModel]:
        results = self.compile()

        if pk is not None:
            queryset = queryset.filter(pk=pk)
        queryset = self.get_filtered_queryset(queryset)

        if results.prefetch_related:
            queryset = queryset.prefetch_related(*results.prefetch_related)
        if results.select_related:
            queryset = queryset.select_related(*results.select_related)
        if not optimizer_settings.DISABLE_ONLY_FIELDS_OPTIMIZATION and (results.only_fields or self.related_fields):
            queryset = queryset.only(*results.only_fields, *self.related_fields)
        if self.annotations:
            queryset = queryset.annotate(**self.annotations)

        mark_optimized(queryset)
        return queryset

    def compile(self) -> CompilationResults:
        results = CompilationResults(only_fields=self.only_fields.copy())

        for name, store in self.select_stores.items():
            # Promote select related to prefetch related if any annotations are needed.
            if store.annotations:
                self.compile_prefetch(name, store, results)
            else:
                self.compile_select(name, store, results)

        for name, store in self.prefetch_stores.items():
            self.compile_prefetch(name, store, results)

        return results

    def compile_select(self, name: str, store: QueryOptimizerStore, results: CompilationResults) -> None:
        results.select_related.append(name)
        nested_results = store.compile()
        results.only_fields.extend(f"{name}{LOOKUP_SEP}{only}" for only in nested_results.only_fields)
        results.select_related.extend(f"{name}{LOOKUP_SEP}{select}" for select in nested_results.select_related)
        for prefetch in nested_results.prefetch_related:
            prefetch.add_prefix(name)
            results.prefetch_related.append(prefetch)

    def compile_prefetch(self, name: str, store: QueryOptimizerStore, results: CompilationResults) -> None:
        queryset = self.get_prefetch_queryset(store.model)
        optimized_queryset = store.optimize_queryset(queryset)
        results.prefetch_related.append(Prefetch(name, optimized_queryset))

    def get_prefetch_queryset(self, model: type[TModel]) -> QuerySet[TModel]:
        return model._default_manager.all()

    def get_filtered_queryset(self, queryset: QuerySet[TModel]) -> QuerySet[TModel]:
        object_type: Optional[DjangoObjectType] = get_global_registry().get_type_for_model(queryset.model)
        if callable(getattr(object_type, "filter_queryset", None)):
            return object_type.filter_queryset(queryset, self.info)  # type: ignore[union-attr]
        return queryset  # pragma: no cover

    @property
    def complexity(self) -> int:
        value: int = 0
        for store in self.select_stores.values():
            value += store.complexity
        for store in self.prefetch_stores.values():
            value += store.complexity
        return value + len(self.select_stores) + len(self.prefetch_stores)

    def __add__(self, other: QueryOptimizerStore) -> QueryOptimizerStore:
        self.only_fields += other.only_fields
        self.related_fields += other.related_fields
        self.annotations.update(other.annotations)
        self.select_stores.update(other.select_stores)
        self.prefetch_stores.update(other.prefetch_stores)
        return self

    def __str__(self) -> str:
        results = self.compile()
        only = ",".join(results.only_fields)
        select = ",".join(results.select_related)
        prefetch = ",".join(item.prefetch_to for item in results.prefetch_related)
        return f"{only=}|{select=}|{prefetch=}"
