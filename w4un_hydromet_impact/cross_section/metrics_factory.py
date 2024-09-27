"""
This module provides factory methods for metrics.
"""
from enum import Enum
from typing import Type

from prometheus_client import CollectorRegistry, REGISTRY, Counter

# label name for event counters
EVENT_LABEL_NAME = 'type'
# label name for object-based counters
OBJECT_LABEL_NAME = 'action'


class LabelEnum(Enum):
    """
    Enum for labels of counters.
    """


# event-based counting

class EventCounterTypes(LabelEnum):
    """
    Supported counting types for event counters.
    AVAILABLE: number of handled events
    FAILURE: number of events causing an error
    SUCCESSFUL: number of successfully handled events
    """
    AVAILABLE = 'available'
    FAILURE = 'failure'
    SUCCESSFUL = 'successful'


def create_event_counter(name: str, description: str, registry: CollectorRegistry = REGISTRY) -> Counter:
    """
    Creates an event counter.
    :param name: the name
    :param description: the description
    :param registry: the registry to be used
    :return: the counter
    """
    return _create_counter(name, description, EVENT_LABEL_NAME, EventCounterTypes, registry)


# object-based counting

class ObjectCounterTypes(LabelEnum):
    """
    Supported counting types for object counters.
    STORED: number of stored objects
    """
    STORED = 'stored'


def create_object_counter(name: str, description: str, registry: CollectorRegistry = REGISTRY) -> Counter:
    """
    Creates an object counter.
    :param name: the name
    :param description: the description
    :param registry: the registry to be used
    :return: the counter
    """
    return _create_counter(name, description, OBJECT_LABEL_NAME, ObjectCounterTypes, registry)


# auxiliary methods

def _create_counter(name: str, description: str, label_name: str, label_enum: Type[LabelEnum],
                    registry: CollectorRegistry) -> Counter:
    """
    Creates a counter.
    :param name: the name
    :param description: the description
    :param label_name: the name of the label
    :param label_enum: the enum defining the supported attributes
    :param registry: the registry to be used
    :return: the counter
    """
    result = Counter(name, description, [label_name], registry=registry)

    # initialize supported labels
    for label_value in iter(label_enum):
        result.labels(label_value.value)

    return result
