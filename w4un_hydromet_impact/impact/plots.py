# type: ignore
"""
This module provides functions to plot impact data.
"""
import logging
import os
from typing import Tuple, Optional

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.figure import Figure

import climada.entity
from climada.engine import Impact
from climada.engine.forecast import Forecast
from w4un_hydromet_impact.cross_section.exceptions import ClimadaError
from w4un_hydromet_impact.exchange.buckets import s3_location_for_impact_file
from w4un_hydromet_impact.fabio import S3Location
from w4un_hydromet_impact.impact.file_names import build_file_name_from_impact_forecast
from w4un_hydromet_impact.util.uploads import upload_figure

logger = logging.getLogger(__name__)

MCH_ENSEMBLE_NUMBER = 21
PATH_AUX: str = '/src/climada4mch/climada4mch/'


def plot_impact_forecast(impact_forecast: Forecast, impact_type: str) -> tuple[S3Location, S3Location]:
    """
    Plots the results of the impact calculation (map and histogram) and stores them
    in S3's ch.meteoswiss.hydrometimpact.impact bucket.
    """

    # save map of impact forecast
    map_plot = _plot_impact_map(impact_forecast, impact_type)
    file_name_map = build_file_name_from_impact_forecast(impact_forecast,
                                                         impact_type,
                                                         'map.jpeg')
    s3_location_map = s3_location_for_impact_file(file_name_map)
    upload_figure(map_plot, s3_location_map)

    # save histogram of impact forecast
    histogram_plot = _plot_impact_histogram(impact_forecast, impact_type)
    file_name_histogram = build_file_name_from_impact_forecast(impact_forecast,
                                                               impact_type,
                                                               'histogram.png')
    s3_location_histogram = s3_location_for_impact_file(file_name_histogram)
    upload_figure(histogram_plot, s3_location_histogram)

    return s3_location_map, s3_location_histogram


def _plot_impact_map(impact_forecast: Forecast, impact_type: str) -> Figure:
    """
    Plots the specified impact forecast as a map.
    :param impact_forecast: the impact forecast
    :param impact_type: the impact type
    :return: a figure representing the plotted map
    """
    logger.info('Trying to plot impact forecast as map.')

    forecast_name = impact_forecast.summary_str()
    try:
        # avoid saving and closing the plotted figure directly because we want to upload it into S3
        return impact_forecast.plot_imp_map(save_fig=False, close_fig=False,
                                            explain_str=_transform_to_description(impact_type))[0][0].figure
    except Exception as error:
        raise ClimadaError(f'Cannot plot impact map: {forecast_name}_{impact_type}') from error


def _plot_impact_histogram(impact_forecast: Forecast, impact_type: str) -> Figure:
    """
    Plots the specified impact forecast as a histogram.
    :param impact_forecast: the impact forecast
    :param impact_type: the impact type
    :return: a figure representing the plotted histogram
    """
    logger.info('Trying to plot impact forecast as histogram.')

    forecast_name = impact_forecast.summary_str()
    try:
        # avoid saving and closing the plotted figure directly because we want to upload it into S3
        plot = impact_forecast.plot_hist(save_fig=False, close_fig=False,
                                         explain_str=_transform_to_description(impact_type))
        return plot.figure
    except Exception as error:
        raise ClimadaError(f'Cannot plot impact histogram: {forecast_name}_{impact_type}') from error


def _transform_to_description(string: str) -> str:
    """
    Transforms the specified string to a description by replacing underscores with spaces.
    """
    return str.replace(string, '_', ' ')


def _reshape_imps(imp: Impact, n_ens: int) -> Impact:
    """
    reshape "linearized" impact events into matrix n_ens x n_lt. strictly only necessary
    form impact objects that have various lead times and ensemble realizations mixed together.
    :param imp:
    :param n_ens:
    :return:
    """
    n_lt = int(imp.imp_mat.shape[0] / n_ens)
    return imp.imp_mat.A.reshape(n_ens, n_lt, -1)


def _get_impact_percentiles_per_severity_level(imp_list: list,
                                               n_ens: int = MCH_ENSEMBLE_NUMBER,
                                               percentiles: tuple = (10, 50, 90)) -> dict:
    """
    get impact percentiles per severity level, from impacts across all ensemble members

    :param imp_list: list of Impact objects including imp_mat, ordered, for severity levels 2-5
    :param n_ens: number of ensemble members (realizations) in each imp object
    :param percentiles: percentiles for which to compute stats; default  is 10, 50 and 90
    :return dict_imp_perc: with keys 2-5 representing severity levels, and nd-arrays representing corresponding
    percentiles as specified in kwarg percentiles
    """
    dict_impacts = dict(
        zip(range(2, 6), [_reshape_imps(imp, n_ens) for imp in imp_list]))

    dict_imp_perc = {}
    for level in range(2, 6):
        dict_imp_perc[level] = np.percentile(dict_impacts[level],
                                             percentiles,
                                             axis=0)
    return dict_imp_perc


def _assign_warnreg2exp(exp: climada.entity.Exposures, gdf_warnregs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Assign exposure elements to one of the warning regions used by forecasters
    :param exp: the exposure to be plotted
    :param gdf_warnregs: the geodataframe containing polygons of the warning regions
    :return: the exposure gdf with additional columns from the matched (spatially joined) warning region columns
    """
    return exp.gdf.sjoin(gdf_warnregs, how='left', predicate='within')


def plot_range_of_aggregate_impact(dict_imp_perc_agg: dict, exp_name: str) -> Figure:
    """
    Plot the range of total exposed elements to all severity levels during an event for the previously
    computed quantiles.

    :param dict_imp_perc_agg: dict with percentile sums of exposed elements per severity level
    :param exp_name: name of exposure to be displayed in plot
    :return: figure with error bar plots
    """
    fig = plt.Figure()
    fig.subplots(1, 1)
    ax = fig.get_axes()

    ax[0].errorbar(
        x=[2, 3, 4, 5],
        y=[dict_imp_perc_agg[level][1, 0] for level in range(2, 6)],
        yerr=np.array([[
            dict_imp_perc_agg[level][1, 0] -
            dict_imp_perc_agg[level][0, 0] for level in range(2, 6)
        ],
            [
                dict_imp_perc_agg[level][2, 0] -
                dict_imp_perc_agg[level][1, 0]
                for level in range(2, 6)
            ]]),
        fmt='r^')
    ax[0].set_xlabel("Severity level")
    ax[0].set_xticks([2, 3, 4, 5])
    ax[0].set_ylabel(f'{exp_name} in \n severity level X or higher')

    fig.suptitle(
            f'Total # of {exp_name} exposed to severity levels, over entire forecast period'
        )
    fig.tight_layout()
    return fig


def _load_shape_file_of_switzerland(single_regions: bool = False, reproj_epsg: Optional[int] = None) -> gpd:
    """
    load shape file of warning regions, either outline (i.e. the shape of Switzerland), or geodataframe of all
    individual regions
    :param single_regions: if True, return individual warning regions; if False, return outline; default False
    :param reproj_epsg: the projection to re-project to (in epsg code)
    :return:
    """
    print("FZFZ: " + os.getcwd())
    print("FZFZ: " + os.path.realpath(__file__))
    gdf_warnregs = gpd.read_file(PATH_AUX + 'MCH_Warnreg_v2_3_LV95_red.shp')

    if reproj_epsg is not None:
        gdf_warnregs = gdf_warnregs.to_crs(epsg=reproj_epsg)
    if single_regions:
        return gdf_warnregs
    return gpd.GeoSeries(shapely.ops.unary_union(
        [geom for geom in gdf_warnregs.geometry]).exterior,
                         crs=gdf_warnregs.crs)


def plot_impact_percentile_maps_of_switzerland(dict_impact_objects: dict,
                                               percentile: int,
                                               exp_label: str) -> Figure:
    """
    Plot "impact maps" of CHE exposures in each of the four severity levels, for a specified percentile.
    :param dict_impact_objects: dict of impact objects referring to exposures in each of the four ewi severity levels
    :param percentile: percentile to be plotted given probabilistic nature of impacts
    :param exp_label: label of exposure to be plotted
    :return: figure with 4 subplots of CHE for each severity level
    """
    border_che = _load_shape_file_of_switzerland(reproj_epsg=4326)

    dict_impact_object_perc = _get_impact_percentiles_per_severity_level(dict_impact_objects.values(),
                                                                         MCH_ENSEMBLE_NUMBER,
                                                                         percentiles=(percentile,))

    axes, fig = create_aggregate_figure()

    vmin = 0
    vmax = np.max(dict_impact_object_perc[2].flatten().max())

    for ax, level in zip(axes, range(2, 6)):
        border_che.plot(facecolor='none', edgecolor='0.5', ax=ax)
        pcm = ax.scatter(dict_impact_objects[2].coord_exp[:, 1],
                         dict_impact_objects[2].coord_exp[:, 0],
                         c=dict_impact_object_perc[level].flatten(),
                         s=0.2,
                         transform=ccrs.PlateCarree(),
                         cmap='PuRd',
                         norm=matplotlib.colors.SymLogNorm(1,
                                                           vmin=vmin,
                                                           vmax=vmax))
        ax.set_title(f'severity level >={level}')

        fig.colorbar(pcm, shrink=0.5, ax=ax)

    fig.suptitle(
        f'{exp_label} exposed, over entire forecast period, ({percentile}th perc.)'
    )

    fig.tight_layout()

    return fig


def plot_impact_percentile_maps_warning_regions_of_switzerland(dict_impact_objects: dict,
                                                               percentile: int,
                                                               exp_label: str) -> Figure:
    """
    Plot "impact maps" of CHE exposures in each of the four severity levels, for a specified percentile, summed up per
    warning region
    :param dict_impact_objects: dict of impact objects referring to exposures in each of the four ewi severity levels
    :param percentile: percentile to be plotted given probabilistic nature of impacts
    :param exp_label: label of exposure to be plotted
    :return: figure with 4 subplots of CHE for each severity level
    """
    dict_impact_object_perc = _get_impact_percentiles_per_severity_level(
        dict_impact_objects.values(),
        MCH_ENSEMBLE_NUMBER,
        percentiles=(percentile, ))

    gdf_warnregs = _load_shape_file_of_switzerland(single_regions=True,
                                                   reproj_epsg=4326)

    centroids = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(dict_impact_objects[2].coord_exp[:, 1],
                                    dict_impact_objects[2].coord_exp[:, 0],
                                    crs='epsg:4326'))
    centroids = centroids.sjoin(gdf_warnregs, how='left',
                                predicate='within').set_index('REGION_NR')
    gdf_warnregs = gdf_warnregs.set_index('REGION_NR')

    axes, fig = create_aggregate_figure()

    for level in range(2, 6):
        centroids[level] = dict_impact_object_perc[level].flatten()
        gdf_warnregs[level] = centroids.groupby('REGION_NR')[level].sum()

    gdf_warnregs.fillna(0, inplace=True)
    vmin = 0
    vmax = np.max(gdf_warnregs[2])

    for ax, level in zip(axes, range(2, 6)):
        gdf_warnregs.plot(facecolor='none', edgecolor='0.5', ax=ax)
        gdf_warnregs.plot(
            level,
            vmin=vmin,
            vmax=vmax,
            ax=ax,
            cmap='PuRd',
            legend=True,
            legend_kwds={"shrink": .5},
        )
        ax.set_title(f'severity level >={level}')

    fig.suptitle(
        f'{exp_label} exposed, over entire forecast period, ({percentile}th perc.)'
    )

    fig.tight_layout()
    return fig


def create_aggregate_figure() -> Tuple[plt.Axes, plt.Figure]:
    fig = plt.Figure(figsize=(15, 11))
    fig.subplots(2,
                 2,
                 sharey=True,
                 sharex=True,
                 subplot_kw=dict(projection=ccrs.PlateCarree())
                 )
    axes = fig.get_axes()
    return axes, fig
