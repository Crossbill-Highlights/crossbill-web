"""
Dependency Injection Container.

A simple but flexible DI container for managing application dependencies.
This container integrates well with FastAPI's dependency injection system.

Usage:
    # Register dependencies
    container = Container()
    container.register(HighlightRepository, PostgresHighlightRepository)
    container.register_factory(UnitOfWork, lambda c: SQLAlchemyUnitOfWork(c.resolve(Session)))

    # Resolve dependencies
    repo = container.resolve(HighlightRepository)

    # Use with FastAPI
    def get_create_flashcard_handler(
        container: Container = Depends(get_container),
    ) -> CreateFlashcardHandler:
        return container.resolve(CreateFlashcardHandler)
"""

import inspect
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TypeVar, overload

T = TypeVar("T")


class DependencyNotFoundError(Exception):
    """Raised when a dependency cannot be resolved."""

    def __init__(self, dependency_type: type) -> None:
        self.dependency_type = dependency_type
        super().__init__(f"No registration found for {dependency_type.__name__}")


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""

    def __init__(self, chain: list[type]) -> None:
        self.chain = chain
        names = " -> ".join(t.__name__ for t in chain)
        super().__init__(f"Circular dependency detected: {names}")


class Container:
    """
    Simple dependency injection container.

    Supports:
    - Type-based registration (interface -> implementation)
    - Factory-based registration (for complex construction)
    - Singleton and transient lifetimes
    - Scoped containers for request-level dependencies
    - Auto-wiring of constructor dependencies
    """

    def __init__(self, parent: "Container | None" = None) -> None:
        self._registrations: dict[type, _Registration] = {}
        self._singletons: dict[type, object] = {}
        self._parent = parent
        self._resolving: set[type] = set()

    def register(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
        *,
        singleton: bool = False,
    ) -> None:
        """
        Register a type mapping.

        Args:
            interface: The interface/abstract type to register
            implementation: The concrete implementation (defaults to interface itself)
            singleton: If True, only one instance is created
        """
        impl = implementation or interface
        self._registrations[interface] = _Registration(
            implementation=impl,
            factory=None,
            singleton=singleton,
        )

    def register_factory(
        self,
        interface: type[T],
        factory: Callable[["Container"], T],
        *,
        singleton: bool = False,
    ) -> None:
        """
        Register a factory function for creating instances.

        Args:
            interface: The interface/abstract type to register
            factory: A function that takes the container and returns an instance
            singleton: If True, the factory is only called once
        """
        self._registrations[interface] = _Registration(
            implementation=None,
            factory=factory,
            singleton=singleton,
        )

    def register_instance(self, interface: type[T], instance: T) -> None:
        """
        Register a pre-created instance (always singleton).

        Args:
            interface: The interface/abstract type to register
            instance: The instance to return when resolved
        """
        self._registrations[interface] = _Registration(
            implementation=None,
            factory=None,
            singleton=True,
        )
        self._singletons[interface] = instance

    @overload
    def resolve(self, interface: type[T]) -> T: ...

    @overload
    def resolve(self, interface: type[T], default: T) -> T: ...

    def resolve(self, interface: type[T], default: object = ...) -> T:  # type: ignore[assignment]
        """
        Resolve a dependency by its interface type.

        Args:
            interface: The interface/abstract type to resolve
            default: Default value if not found (raises if not provided)

        Returns:
            An instance of the registered implementation

        Raises:
            DependencyNotFoundError: If no registration exists and no default
            CircularDependencyError: If circular dependency detected
        """
        # Check for circular dependencies
        if interface in self._resolving:
            raise CircularDependencyError([*list(self._resolving), interface])

        # Check if already a singleton
        if interface in self._singletons:
            return self._singletons[interface]  # type: ignore[return-value]

        # Look up registration
        registration = self._registrations.get(interface)

        # Check parent container if not found
        if registration is None and self._parent is not None:
            return self._parent.resolve(interface, default)  # type: ignore[arg-type]

        # Handle missing registration
        if registration is None:
            if default is not ...:
                return default  # type: ignore[return-value]
            raise DependencyNotFoundError(interface)

        # Track resolution for circular dependency detection
        self._resolving.add(interface)
        try:
            instance = self._create_instance(registration)
        finally:
            self._resolving.discard(interface)

        # Cache singleton
        if registration.singleton:
            self._singletons[interface] = instance

        return instance  # type: ignore[return-value]

    def _create_instance(self, registration: "_Registration") -> object:
        """Create an instance from a registration."""
        if registration.factory is not None:
            return registration.factory(self)

        if registration.implementation is not None:
            return self._auto_wire(registration.implementation)

        raise ValueError("Invalid registration: no factory or implementation")

    def _auto_wire(self, cls: type[T]) -> T:
        """
        Auto-wire constructor dependencies.

        Inspects the __init__ signature and resolves parameters
        from the container.
        """
        sig = inspect.signature(cls.__init__)
        kwargs: dict[str, object] = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            # Skip parameters with defaults if not registered
            if param.annotation is inspect.Parameter.empty:
                continue

            param_type = param.annotation

            # Handle optional types (Union with None)
            origin = getattr(param_type, "__origin__", None)
            if origin is type(None) or (
                hasattr(param_type, "__args__")
                and type(None) in getattr(param_type, "__args__", ())
            ):
                # For optional types, use None as default if not registered
                try:
                    kwargs[name] = self.resolve(param_type)
                except DependencyNotFoundError:
                    if param.default is not inspect.Parameter.empty:
                        kwargs[name] = param.default
                    else:
                        kwargs[name] = None
                continue

            # Required parameter
            if param.default is not inspect.Parameter.empty:
                kwargs[name] = self.resolve(param_type, param.default)
            else:
                kwargs[name] = self.resolve(param_type)

        return cls(**kwargs)  # type: ignore[arg-type]

    def create_scope(self) -> "Container":
        """
        Create a scoped child container.

        Scoped containers inherit registrations from the parent
        but have their own singleton cache. Useful for request-scoped
        dependencies.
        """
        return Container(parent=self)

    @contextmanager
    def scope(self) -> Generator["Container", None, None]:
        """
        Context manager for scoped resolution.

        Example:
            with container.scope() as scoped:
                handler = scoped.resolve(CreateFlashcardHandler)
                result = handler.handle(command)
        """
        scoped = self.create_scope()
        yield scoped

    def has(self, interface: type) -> bool:
        """Check if a type is registered."""
        if interface in self._registrations:
            return True
        if self._parent is not None:
            return self._parent.has(interface)
        return False


class _Registration:
    """Internal registration record."""

    __slots__ = ("factory", "implementation", "singleton")

    def __init__(
        self,
        implementation: type | None,
        factory: Callable[[Container], object] | None,
        singleton: bool,
    ) -> None:
        self.implementation = implementation
        self.factory = factory
        self.singleton = singleton


class _ContainerRegistry:
    """
    Manages the global application container.

    Using a class instead of module-level globals for cleaner state management.
    """

    _instance: Container | None = None

    @classmethod
    def get(cls) -> Container:
        """Get the application container, creating one if needed."""
        if cls._instance is None:
            cls._instance = Container()
        return cls._instance

    @classmethod
    def set(cls, container: Container) -> None:
        """Set the application container."""
        cls._instance = container

    @classmethod
    def reset(cls) -> None:
        """Reset the application container (useful for testing)."""
        cls._instance = None


def get_container() -> Container:
    """
    Get the application container.

    This is the entry point for FastAPI dependency injection.
    """
    return _ContainerRegistry.get()


def set_container(container: Container) -> None:
    """
    Set the application container.

    Call this during application startup to configure dependencies.
    """
    _ContainerRegistry.set(container)


def reset_container() -> None:
    """
    Reset the application container.

    Useful for testing.
    """
    _ContainerRegistry.reset()
