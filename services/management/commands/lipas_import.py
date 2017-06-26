import logging

from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos.collections import GeometryCollection

from services.models.unit_identifier import UnitIdentifier

URLS = {
    'areas': 'http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=lipas:lipas_kaikki_alueet',
    'paths': 'http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=lipas:lipas_kaikki_reitit'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Retrieving all external unit identifiers from the database...')

        # Get all external datasource records from the database
        unit_identifiers = UnitIdentifier.objects.filter(namespace='lipas')

        # Build a lipas_id-indexed dictionary of units
        units_by_lipas_id = {}
        for unit_identifier in unit_identifiers:
            units_by_lipas_id[int(unit_identifier.value)] = unit_identifier.unit

        # Get path and area data from the Lipas WFS
        logger.info('Done.')
        logger.info('Retrieving geodata from Lipas...')
        ds_paths = DataSource(URLS['paths'])
        ds_areas = DataSource(URLS['areas'])
        logger.info('Done.')

        # Ensure the data looks somewhat correct
        if len(ds_paths) != 1 or len(ds_areas) != 1:
            raise ValueError('The LIPAS API returned unexpected data!')

        layers = [ds_paths[0], ds_areas[0]]

        # The Lipas database stores paths and areas as different features
        # which have a common id. We want to store the paths as one
        # GeometryCollection which includes all the small subpaths or areas.

        # This is a dict which will contain GeometryCollections hashed by
        # their Lipas id.
        geometries = {}

        # Iterate through Lipas layers and features
        logger.info('Processing Lipas geodata...')
        for layer in layers:
            for feature in layer:
                logger.debug(feature.fid)

                # Check if the feature's id is in the dict we built earlier
                if feature['id'].value in units_by_lipas_id:
                    logger.debug('found: ' + units_by_lipas_id[feature['id'].value].name_fi)

                    # TODO Check that they surely are the same unit
                    logger.debug('confirm: ' + feature['nimi_fi'].value)

                    # Initialize an empty GeometryCollection if we haven't encountered
                    # this id before. Elsewise just append to the collection.
                    if feature['id'].value in geometries:
                        geometries[feature['id'].value].append(feature.geom.geos)
                    else:
                        geometries[feature['id'].value] = GeometryCollection(feature.geom.geos)

                else:
                    logging.debug('id not found: ' + str(feature['id'].value))

        logger.info('Done. Found {} matches'.format(len(geometries)))

        # Add all geometries we found to the db
        logger.info('Updating geometries in the database...')
        for lipas_id, geometry in geometries.items():
            units_by_lipas_id[lipas_id].geometry = geometry
            units_by_lipas_id[lipas_id].save()

        logger.info('Done.')
