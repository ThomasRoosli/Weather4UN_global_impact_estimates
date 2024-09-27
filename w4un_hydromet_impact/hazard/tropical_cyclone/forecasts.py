from climada_petals.hazard.tc_tracks_forecast import TCForecast

# We use the traditional WMO guidelines for converting between various wind averaging periods
# in tropical cyclone conditions (cf. https://library.wmo.int/doc_num.php?explnum_id=290)
# Our input data is giving the maximum sustained wind speed for ten minute intervals while we need it for one minute
# intervals. In one minute intervals, changes in wind speed are more pronounced, so we need to make the maximum
# sustained wind speed slightly bigger.
WIND_CONVERSION_FACTOR = 1. / 0.88


def create_ensemble_tropical_cyclone_forecast_from_ecmwf(weather_data_path_name: str) -> TCForecast:
    """
    Creates a TCForecast object based on input files containing tropical cyclone weather data in ECMWF format.
    Only tracks which are part of ensemble runs are kept.
    On the way, we have to correct the maximum sustained wind speed because it is delivered in a different convention
    than we need
    :param weather_data_path_name: the location of the input files
    :return: the TCForecast object with corrected wind speed corresponding to the ensemble part of the input
    """
    tc_forecast = TCForecast()
    if weather_data_path_name == '':
        tc_forecast.fetch_ecmwf()
    else:
        tc_forecast.fetch_ecmwf(files=weather_data_path_name)

    _correct_max_sustained_wind_speed(tc_forecast)

    return _reduce_to_ensemble_tracks(tc_forecast)


def _correct_max_sustained_wind_speed(tc_forecast: TCForecast,
                                      wind_conversion_factor: float = WIND_CONVERSION_FACTOR) -> None:
    """
    Converts the maximum sustained wind speed by a given factor. The sustained wind speed is defined as the wind speed
    which has not been underrun by any measurement within a given time interval.
    Note that the operation of multiplying by a constant factor is simplifying reality and a more complex method
    should be used eventually
    :param tc_forecast: The tracks object to which the modification is applied
    :param wind_conversion_factor: The factor by which the maximum sustained wind will be modified
    :return:
    """
    for dataset in tc_forecast.data:
        dataset['max_sustained_wind'] *= wind_conversion_factor


def _reduce_to_ensemble_tracks(tc_forecast: TCForecast) -> TCForecast:
    return tc_forecast.subset({'is_ensemble': True})


def filter_and_group_tropical_cyclone_forecast(tc_forecast: TCForecast, only_retain_named_storms: bool = True) \
        -> list[TCForecast]:
    """
    Takes a TCForecast object and creates a list of TCForecast objects from it so that each element of the list is
    grouped by a certain storm name.
    Example: If the data inside the TCForecast object has named storms Xaver and Erika (among other unnamed
    storms), you will receive a list of two TCForecast objects, in which the first element groups all Xaver elements
    and the second all Erika elements (or vice versa).
    :param tc_forecast: input TCForecast tracks object which will be filtered and grouped
    :param only_retain_named_storms: has to be true for now, false is not implemented
    :return: list of TCForecast objects in which each list element belongs to a certain storm name
    """

    if only_retain_named_storms:
        unique_names_of_named_storms: set[str] = _determine_unique_names_of_named_storms(tc_forecast)
        filtered_and_grouped_tc_forecasts: list[TCForecast] = [
            tc_forecast.subset({'name': name}) for name in unique_names_of_named_storms
        ]
    else:
        filtered_and_grouped_tc_forecasts = _filter_and_group_established_storms(tc_forecast)
    return filtered_and_grouped_tc_forecasts


def _determine_unique_names_of_named_storms(tc_forecast: TCForecast) -> set[str]:
    """
    Examines whether the individual data members of the input TCForecast they belong to a named storm.
    If yes, the storm names are added to a result set
    :param tc_forecast: The TCForecast object under examination
    :return: a set of storm names, e.g. {'Xaver', 'Erika'}
    """
    return {data.attrs['name'] for data in tc_forecast.data if data.attrs['name'] != data.sid}


def _filter_and_group_established_storms(tc_forecast: TCForecast) -> list[TCForecast]:
    """
    Not part of MVP, therefore implementation/refactoring postponed.
    :param tc_forecast:
    :return:
    """
    # todo roo refactor and test
    # names = [data.attrs['name'] for data in tracks.data]
    # tracks_list = []
    # # get only events that are present in all members
    # name_me = np.unique(names, return_counts=True)[1] == 51
    # storms_all_members = np.unique(names)[name_me]
    #
    #
    # for name in storms_all_members:
    #     track_subset_temp = tracks.subset({'name': name})
    #     tracks_exists_at_init = True
    #     for data_j in track_subset_temp.data:
    #         tracks_exists_at_init = (tracks_exists_at_init and (data_j.run_datetime == data_j.time[0]))
    #     if tracks_exists_at_init:
    #         tracks_list.append(track_subset_temp)
    # return tracks_list
    raise NotImplementedError


def make_name_and_sid_unique(tc_forecast: TCForecast) -> None:
    """
    The names of the TCForecast data have to be unique for further processing, so we add the ensemble number to the name
    to make it unique. Also, we are overwriting the sid-attribute (something like a02 -> second storm in the Atlantic
    ocean) by the corresponding name.
    Note: For established and unnamed storms, the CLIMADA sid and name are the same,
    and for named storms they are different (Xaver vs. a02).
    :param tc_forecast: input TCForecast tracks object which should be modified
    :return:
    """
    for dataset in tc_forecast.data:
        dataset.attrs['name'] = dataset.name + '_' + str(dataset.ensemble_number)
        dataset.attrs['sid'] = dataset.name
