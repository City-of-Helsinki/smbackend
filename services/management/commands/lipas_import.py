from urllib.parse import urlencode
import logging

from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos.collections import GeometryCollection

from services.models.unit_identifier import UnitIdentifier

TYPES = {
    'paths': 'lipas:lipas_kaikki_reitit',
    'areas': 'lipas:lipas_kaikki_alueet'
}

WFS_BASE = 'http://lipas.cc.jyu.fi/geoserver/lipas/ows'

logger = logging.getLogger(__name__)


class MiniWFS:
    def __init__(self, base_url):
        self.base_url = base_url

        self.payload = {}
        self.payload['version'] = '1.0.0'
        self.payload['service'] = 'WFS'

    def get_feature(self, **params):
        payload = self.payload.copy()
        payload['request'] = 'GetFeature'
        payload['typeName'] = params.get('type_name')
        payload['maxFeatures'] = params.get('max_features')
        payload['cql_filter'] = params.get('cql_filter')

        return self._url(payload)

    def _url(self, payload):
        # Clear values set to None
        for key in list(payload):
            if payload[key] is None:
                del payload[key]

        return "{}?{}".format(self.base_url, urlencode(payload))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--max-features',
            action='store',
            type=int,
            help='This is applied to paths and areas separately.'
        )

        parser.add_argument(
            '-m', '--muni-id',
            action='append',
            type=int,
            help='Filter results by municipality. '
        )

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

        wfs = MiniWFS(WFS_BASE)
        max_features = options.get('max_features')
        muni_filter = options.get('muni_id')

        if muni_filter is not None:
            muni_filter = ' OR '.join(["kuntanumero = '{}'".format(id_) for id_ in muni_filter])

        layers = {}
        for key, val in TYPES.items():
            url = wfs.get_feature(
                type_name=val,
                max_features=max_features,
                cql_filter=muni_filter
            )

            layers[key] = DataSource(url)[0]

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

                def clean_name(name):
                    import re
                    name = name.lower().strip()
                    name = re.sub(r'\s{2,}', ' ', name)
                    return name

                if clean_name(feature['nimi_fi'].value) != clean_name(unit.name_fi):
                    logger.warning('id {} has non-matching name fields.\n'
                                   'Lipas: "{}"\n'
                                   'db: "{}"'.format(lipas_id, feature['nimi_fi'].value, unit.name_fi))

                try:
                    # Initialize an empty GeometryCollection if we haven't encountered
                    # this id before. Elsewise just append to the collection.
                    if lipas_id in geometries:
                        geometries[lipas_id].append(feature.geom.geos)
                    else:
                        geometries[lipas_id] = GeometryCollection(feature.geom.geos)

                except GDALException as err:
                    # We might be dealing with something weird that the Python GDAL lib doesn't handle.
                    # One example is a CurvePolygon as defined here http://www.gdal.org/ogr__core_8h.html
                    logger.error('Error while processing a geometry: {}'.format(err))

        logger.info('Found {} matches.'.format(len(geometries)))

        # Add all geometries we found to the db
        logger.info('Updating geometries in the database...')
        for lipas_id, geometry in geometries.items():
            unit = units_by_lipas_id[lipas_id]
            # Simplify our GeometryCollections as much as possible
            unit.geometry = geometry.unary_union
            unit.save()
