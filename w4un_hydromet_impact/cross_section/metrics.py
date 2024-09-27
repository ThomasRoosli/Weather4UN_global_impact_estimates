"""
This module defines Prometheus-based metrics for Climada4MCH.

See https://github.com/prometheus/client_python for documentation of using Prometheus with Python.
"""
from functools import wraps
from typing import TypeVar, Any, Callable, Optional, Type

from prometheus_client import Counter

from w4un_hydromet_impact.cross_section.metrics_factory import create_event_counter, EventCounterTypes, EVENT_LABEL_NAME, \
    create_object_counter, ObjectCounterTypes, OBJECT_LABEL_NAME, LabelEnum

# event-based counter for handling weather data events (ExtractHazard)
weather_data_event_counter = create_event_counter('weather_data_events', 'Number of weather data events')
# event-based counter for handling impact events (CalculateImpact)
impact_event_counter = create_event_counter('impact_events', 'Number of impact events')
# object-based counter for actions on hazard objects
hazard_object_counter = create_object_counter('hazard_objects', 'Actions with hazard objects')

# any label enum
L = TypeVar('L', bound=LabelEnum)


# event-based counting

def event_counting(counter: Counter) -> Any:
    """
    Decorates a function call using a counter for counting the number of calls as well
    as the number of successful or failing calls thereof.
    :param counter: the counter
    """

    def counter_decorator(func: Callable[..., Optional[Any]]) -> Callable[..., Optional[Any]]:
        @wraps(func)
        def counter_wrapper(*args: Any, **kwargs: Any) -> Any:
            counter.labels(EventCounterTypes.AVAILABLE.value).inc()
            try:
                result = func(*args, **kwargs)
            except BaseException as error:
                counter.labels(EventCounterTypes.FAILURE.value).inc()
                raise error
            counter.labels(EventCounterTypes.SUCCESSFUL.value).inc()
            return result

        return counter_wrapper

    return counter_decorator


def get_event_counts(counter: Counter, name: str) -> dict[EventCounterTypes, float]:
    """
    Returns the numbers per type of the specified event counter.
    :param counter: the event counter
    :param name: the (expected) base name of the counter
    :return: the numbers
    """
    return _get_numbers(counter, EventCounterTypes, name, EVENT_LABEL_NAME)


# object-based counting

def object_counting(counter: Counter, action: ObjectCounterTypes) -> Any:
    """
    Decorates a function call using a counter for counting the number of calls
    and associates them with the specified action.
    """

    if action not in ObjectCounterTypes:
        raise AssertionError(f'Unknown action specified for object counting: {action}')

    def counter_decorator(func: Callable[..., Optional[Any]]) -> Callable[..., Optional[Any]]:
        @wraps(func)
        def counter_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            counter.labels(action.value).inc()

            return result

        return counter_wrapper

    return counter_decorator


def get_object_counts(counter: Counter, name: str) -> dict[ObjectCounterTypes, float]:
    """
    Returns the numbers per actions on the specified counter.
    :param counter: the object-based counter
    :param name: the (expected) base name of the counter
    :return: the numbers
    """
    return _get_numbers(counter, ObjectCounterTypes, name, OBJECT_LABEL_NAME)


# common functions

def _get_numbers(counter: Counter, label_type: Type[L], name: str, label_name: str) -> dict[L, float]:
    """
    Returns the numbers of calls on the specified counter depending on the specified label.
    :param counter: the counter
    :param label_type: the type of the enum specifying the supported labels
    :param name: the (expected) base name of the counter
    :param label_name: the label name used to count
    :return: the numbers
    """
    metrics = list(counter.collect())
    assert len(metrics) == 1
    assert metrics[0].name == name

    # init
    result = dict[L, float]()
    for label_value in iter(label_type):
        result[label_value] = 0

    for sample in metrics[0].samples:
        if sample.name == name + '_total':
            label = sample.labels[label_name]
            if label:
                result[label_type(label)] = sample.value

    return result
