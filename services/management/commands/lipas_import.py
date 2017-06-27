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


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Retrieving all external unit identifiers from the database...')

        # Get all external datasource records from the database
        unit_identifiers = UnitIdentifier.objects.filter(namespace='lipas')

        # Build a lipas_id-indexed dictionary of units
        units_by_lipas_id = {}
        for unit_identifier in unit_identifiers:
            units_by_lipas_id[int(unit_identifier.value)] = unit_identifier.unit

        logger.info('Retrieved {} objects.'.format(len(unit_identifiers)))

        # Get path and area data from the Lipas WFS
        logger.info('Retrieving geodata from Lipas...')
        layers = {}
        layers['paths'] = DataSource(URLS['paths'])[0]
        layers['areas'] = DataSource(URLS['areas'])[0]
        logger.info('Retrieved {} path and {} area features.'.format(len(layers['paths']), len(layers['areas'])))

        # The Lipas database stores paths and areas as different features
        # which have a common id. We want to store the paths as one
        # GeometryCollection which includes all the small subpaths or areas.

        # This is a dict which will contain GeometryCollections hashed by
        # their Lipas id.
        geometries = {}

        # Iterate through Lipas layers and features
        logger.info('Processing Lipas geodata...')
        for _, layer in layers.items():
            for feature in layer:
                logger.debug(feature.fid)

                # Check if the feature's id is in the dict we built earlier
                lipas_id = feature['id'].value
                unit = units_by_lipas_id.get(lipas_id)
                if not unit:
                    logging.debug('id not found: {}'.format(lipas_id))
                    continue

                logger.debug('found id: '.format(lipas_id))

                if feature['nimi_fi'].value != unit.name_fi:
                    logger.warning('id {} has non-matching name fields.\n'
                                   'Lipas: "{}"\n'
                                   'db: "{}"'.format(lipas_id, feature['nimi_fi'].value, unit.name_fi))

                # Initialize an empty GeometryCollection if we haven't encountered
                # this id before. Elsewise just append to the collection.
                if lipas_id in geometries:
                    geometries[lipas_id].append(feature.geom.geos)
                else:
                    geometries[lipas_id] = GeometryCollection(feature.geom.geos)

        logger.info('Found {} matches.'.format(len(geometries)))

        # Add all geometries we found to the db
        logger.info('Updating geometries in the database...')
        for lipas_id, geometry in geometries.items():
            unit = units_by_lipas_id[lipas_id]
            # Simplify our GeometryCollections as much as possible
            unit.geometry = geometry.unary_union
            unit.save()
