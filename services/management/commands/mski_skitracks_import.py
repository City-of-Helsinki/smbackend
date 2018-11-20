# -*- coding: utf-8 -*-

# Note: this module expects the names of
# the skiing tracks to remain the same.
# Otherwise duplicate tracks are introduced.

from optparse import make_option
import logging
from django.utils import timezone
from django.utils.translation import ugettext_noop as _

import re

from django.core.management.base import BaseCommand
from django.core.exceptions import DoesNotExist
from django import db
from django.contrib.gis.geos import MultiLineString, LineString, Point, GEOSGeometry

import django.contrib.gis
from django.contrib.gis.gdal import DataSource

from services.models import Unit, UnitConnection, Service
from munigeo.models import Address

ADDRESS_RE = re.compile('([^0-9]+) ([0-9]+)([^0-9]*)')


def gk25_converter(a=0, b=0, c=1, d=0, e=0, f=1):
    def converter(x, y):
        return (
            (b + (e * y) + (f * x)),
            (a + (c * y) + (d * x)))
    return converter


espoo_coordinates_to_gk25 = gk25_converter(
    a=6600290.731951121200000,
    b=25443205.726901203000000,
    c=0.999869662254702,
    d=-0.015128383929030,
    e=0.015134113397130,
    f=0.999867560105837)

helsinki_coordinates_to_gk25 = gk25_converter(
    a=6654650.14636,
    b=25447166.49457,
    c=0.99998725362,
    d=-0.00120230340,
    e=0.00120230340,
    f=0.99998725362)

HELSINKI_GROUPS = {
    'Hermanni - Viikki': 'itä',
    'Herttoniemi 1.0 km': 'itä',
    'Herttoniemi 2.0 km': 'itä',
    'Hevossalmen uimaranta - Yliskylä': 'itä',
    'Laajasalo kuntorata': 'itä',
    'Malmin lentokenttä 5.7 km': 'itä',
    'Merirastila': 'itä',
    'Mustavuori - Talosaari/Husö': 'itä',
    'Mustavuori - Vuosaarensilta': 'itä',
    'Mustavuori 2.125 km': 'itä',
    'Mustavuori 1.0 km': 'itä',
    'Mustikkamaa': 'itä',
    'Paloheinä 1.8 km': 'länsi',
    'Sakarinmäen koulu': 'itä',
    'Salmi 3 km': 'itä',
    'Siltamäki': 'itä',
    'Taivaskallio - Tuomarinkartano - Paloheinä 11.5 km': 'länsi',
    'Tali 6.5 km': 'länsi',
    'Tapulin kuntorata': 'itä',
    'Herttoniemi 3.0 5.0 km': 'itä',
    'Kannelmäki peltolatu': 'länsi',
    'Kivikko 3.745 km': 'itä',
    'Kivinokka - Viikki 4.8 km': 'itä',
    'Lassila - Kannelmäki - Keskuspuisto': 'länsi',
    'Malminkartano': 'länsi',
    'Maunulan kuntorata 1.5 km': 'länsi',
    'Oulunkylä kuntorata': 'länsi',
    'Lumetettu latu: Paloheinä 1 km': 'länsi',
    'Paloheinä 3.0 km': 'länsi',
    'Paloheinä 5.2 km': 'länsi',
    'Paloheinä 7.5 km': 'länsi',
    'Paloheinä metsälenkki': 'länsi',
    'Paloheinä peltolatu': 'länsi',
    'Paloheinä vetokoiralatu': 'länsi',
    'Pirkkola - Laakso 5.5 km': 'länsi',
    'Pirkkola - Pitkäkoski 5.5 km': 'länsi',
    'Pirkkola 3.0 km': 'länsi',
    'Pitkäkoski - Niskala': 'länsi',
    'Pitäjänmäki kuntorata': 'länsi',
    'Pukinmäki peltolatu': 'länsi',
    'Tali - Haaga - Pirkkola': 'länsi',
    'Tuomarinkylä peltolatu': 'länsi',
    'Salmi 3 km': 'salmi',
    'Salmi 5 km': 'salmi',
    'Salmi 6 km': 'salmi',
    'Salmi 10 km': 'salmi',
    'Luukki peltolatu': 'luukki',
    'Luukki Golf': 'luukki',
    'Pirttimäki 3 km': 'pirttimäki',
    'Pirttimäki 6.4 km': 'pirttimäki',
    'Pirttimäki 8.3 km': 'pirttimäki'
}

ILLUMINATED = _('_illuminated')
NOT_ILLUMINATED = _('_not_illuminated')
PARTLY_ILLUMINATED = _('_partly_illuminated')
UNKNOWN = _('_unknown')
CLASSIC_OR_FREE = _('_classic/free')
CLASSIC = _('_classic')
FREE = _('_free')
SKATING_IN_PARTS = _('_skating_in_parts')

HELSINKI_LIGHTING = {
    'Valaistu': ILLUMINATED,
    'Ei valaistu': NOT_ILLUMINATED,
    'Osittain valaistu': PARTLY_ILLUMINATED,
    None: UNKNOWN,
    '': UNKNOWN
}

ESPOO_LIGHTING = {
    'Valaistu latu': ILLUMINATED,
    'Valaistu': ILLUMINATED,
    'Ei valaistu': NOT_ILLUMINATED,
    'Valaisematon latu': NOT_ILLUMINATED,
    'Valaisematon latu,ei poh': NOT_ILLUMINATED,
    'Osittain valaistu latu': PARTLY_ILLUMINATED,
    '': UNKNOWN,
    None: UNKNOWN
}

HELSINKI_TECHNIQUES = {
    'Perinteinen/Vapaa': CLASSIC_OR_FREE,
    'Vapaa/Perinteinen': CLASSIC_OR_FREE,
    'Perinteinen': CLASSIC,
    'Vapaa': FREE,
    'Osittain luistelu': SKATING_IN_PARTS,
    None: UNKNOWN,
    '': UNKNOWN
}

VANTAA_MAINTENANCE_GROUPS = {
    'keski': 'keski',
    'l�nsi': 'länsi',
    'it�': 'itä'
}


def _report_counts(municipality, created, updated):
    print("Imported skiing tracks for {}:\n{} created / {} updated".format(
        municipality, created, updated))


class Command(BaseCommand):
    help = "Import ski track units from GeoJSON derived from mSki"
    option_list = list(BaseCommand.option_list + (
        make_option('--helsinki-file', dest='helsinki_filename', help='input filename'),
        make_option('--vantaa-file', dest='vantaa_filename', help='input filename'),
        make_option('--espoo-file', dest='espoo_filename', help='input filename'),
    ))

    def clean_text(self, text):
        # text = text.replace('\n', ' ')
        # text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        text = re.sub(r'\s\s+', ' ', text, re.U)
        # remove nil bytes
        text = text.replace('\u0000', ' ')
        text = text.strip()
        return text

    def unit_defaults(self, geometry, point, extra_fields, street_address, address_zip, www_url):
        return {
            'provider_type': 101,
            'last_modified_time': timezone.now(),
            'geometry': geometry,
            'location': point,
            'data_source': 'manual_import',
            'extensions': extra_fields,
            'street_address': street_address,
            'address_zip': address_zip,
            'www_url': www_url
        }

    def _create_or_update_unit(self, uid, name, defaults):
        units = Unit.objects.filter(name_fi=name, services=self.ski_service)
        if len(units) == 1:
            units.update(**defaults)
            units[0].services.add(self.ski_service)
            return (uid, False, units[0])
        elif len(units) == 0:
            print('no name match for', name)
            unit = Unit.objects.create(
                name_fi=name,
                id=uid,
                **defaults)
            unit.services.add(self.ski_service)
            return (uid - 1, True, unit)
        else:
            print('Error, too many matches for {}'.format(name))
            return (uid, False, None)

    @db.transaction.atomic
    def import_helsinki_units(self, filename):
        ds = DataSource(filename)
        assert len(ds) == 1
        uid = self.get_lowest_high_unit_id()

        def get_lighting(p):
            return HELSINKI_LIGHTING[p.get('VALAISTUS')]

        def get_technique(p):
            return HELSINKI_TECHNIQUES[p.get('TYYLI')]

        def get_length(p):
            len = p.get('PITUUS')
            if len(len) == 0:
                len = None
            return len

        def get_maintenance_group(p):
            n = p.get('NIMI')
            return HELSINKI_GROUPS[n]

        created = 0
        updated = 0
        lyr = ds[0]
        for feat in lyr:
            properties = feat
            maintenance_organization = '91'
            if properties.get('NIMI') == 'Siltamäki':
                maintenance_organization = '92'
            elif properties.get('NIMI').find('Pirttimäki') == 0:
                maintenance_organization = '49'
            try:
                maintenance_group = get_maintenance_group(properties)
            except KeyError:
                print('Missing maintenance group for', properties.get('NIMI'), ', skipping')
                continue
            extra_fields = {
                'lighting': get_lighting(properties),
                'skiing_technique': get_technique(properties),
                'length': get_length(properties),
                'maintenance_group': maintenance_group,
                'maintenance_organization': maintenance_organization
            }
            if type(feat.geom) == django.contrib.gis.gdal.geometries.MultiLineString:
                multilinestring = GEOSGeometry(feat.geom.wkt)
            else:
                multilinestring = MultiLineString(GEOSGeometry(feat.geom.wkt))
            converted_multilinestring_coords = []
            for line in multilinestring:
                converted_multilinestring_coords.append(
                    LineString(tuple((helsinki_coordinates_to_gk25(point[0], point[1]) for point in line))))

            converted_multilinestring = (
                MultiLineString((converted_multilinestring_coords), srid=3879))

            street_address = properties.get('address')
            www_url = properties.get('www_url')
            address_zip = properties.get('zip')
            if len(street_address) == 0:
                street_address = None
            if len(www_url) == 0:
                www_url = None
            if len(address_zip) == 0:
                address_zip = None

            municipality = properties.get('city')
            if municipality is None or len(municipality) == 0:
                municipality = 'helsinki'
            point = None
            if street_address:
                point = self.geocode_street_address(street_address, municipality)
            if point is None:
                point = Point(converted_multilinestring[0][0], converted_multilinestring[0][1], srid=3879)

            defaults = self.unit_defaults(
                converted_multilinestring,
                point,
                extra_fields,
                street_address, address_zip, www_url
            )
            defaults['municipality_id'] = municipality
            defaults['organization_id'] = 91
            uid, did_create, unit = self._create_or_update_unit(uid, properties['NIMI'], defaults)
            if did_create:
                created += 1
            else:
                updated += 1
            if street_address:
                self.add_public_transportation_connection(unit, street_address, municipality)

        _report_counts('helsinki', created, updated)

    def get_lowest_high_unit_id(self):
        MAX_PK = 2147483647
        result = Unit.objects.filter(pk__gt=MAX_PK - 100000).order_by('pk')
        if len(result) == 0:
            return MAX_PK
        return result.first().pk - 1

    @db.transaction.atomic
    def import_vantaa_units(self, filename):
        ds = DataSource(filename)
        assert(len(ds) == 1)
        lyr = ds[0]
        uid = self.get_lowest_high_unit_id()

        created = 0
        updated = 0
        for feat in lyr:
            assert feat.geom_type == 'LineString'
            if type(feat.geom) == django.contrib.gis.gdal.geometries.MultiLineString:
                multilinestring = GEOSGeometry(feat.geom.wkt)
            else:
                multilinestring = MultiLineString(GEOSGeometry(feat.geom.wkt))

            length = re.sub('[^0-9]+km', '', feat.get('pituus'))
            if len(length) == 0:
                length = None
            extra_fields = {
                'maintenance_group': VANTAA_MAINTENANCE_GROUPS[feat.get('piiri_nimi')],
                'maintenance_organization': '92',
                'length': length,
                'origin_id': str(feat.get('latu_id'))
            }
            defaults = self.unit_defaults(
                multilinestring,
                Point(feat.geom[0][0], feat.geom[0][1]),
                extra_fields, None, None, None)
            defaults['municipality_id'] = 'vantaa'
            defaults['organization_id'] = 92
            uid, did_create, unit = self._create_or_update_unit(uid, feat.get('nimi'), defaults)
            if did_create:
                created += 1
            else:
                updated += 1
        _report_counts('vantaa', created, updated)

    def geocode_street_address(self, street_address, municipality):
        street_address_match = ADDRESS_RE.match(street_address)
        street = street_address_match.group(1)
        number = street_address_match.group(2)
        letter = street_address_match.group(3)
        try:
            a = Address.objects.get(
                street__municipality_id=municipality,
                street__name_fi=street,
                number=number)
            return a.location
        except DoesNotExist:
            print('address not found', street_address_match.group(1), '--', street_address_match.group(2))
            return None

    def add_public_transportation_connection(self, unit, street_address, municipality):
        string = '{},+{}'.format(street_address.lower(), municipality).replace(' ', '+')
        url = 'http://www.reittiopas.fi/{lang}/?to_in={address}'
        defaults = {
            "name_en": "Public transport to here",
            "name_sv": "Kollektivtrafik till platsen",
            "name_fi": "Joukkoliikenneyhteydet tänne",
            "www_url_en": url.format(lang='en', address=string),
            "www_url_sv": url.format(lang='sv', address=string),
            "www_url_fi": url.format(lang='fi', address=string),
            "contact_person": None,
            "email": None,
            "phone": None,
            "phone_mobile": None
        }
        return UnitConnection.objects.update_or_create(
            type=215,
            section='traffic',
            unit=unit,
            defaults=defaults)

    @db.transaction.atomic
    def import_espoo_units(self, filename):
        ds = DataSource(filename)
        assert len(ds) == 1
        uid = self.get_lowest_high_unit_id()
        lyr = ds[0]
        created = 0
        updated = 0
        for feat in lyr:
            if feat.get('NIMI') in [
                    'Tali 6.5 km',
                    'Pirttimäki 3.0 km',
                    'Pirttimäki 6.4 km',
                    'Pirttimäki 8.3 km']:
                # These are Helsinki's tracks,
                # and the maintainer is set to Espoo in the Helsinki importer
                continue
            name = feat.get('NIMI')
            if name.find('Aurattu ulkoilureitti') == 0:
                # Do not import these
                continue
            if type(feat.geom) == django.contrib.gis.gdal.geometries.MultiLineString:
                multilinestring = GEOSGeometry(feat.geom.wkt)
            else:
                multilinestring = MultiLineString(GEOSGeometry(feat.geom.wkt))
            if lyr.srs is not None and lyr.srs['PROJCS'] == 'ETRS89_TM35FIN_E_N':
                # support layers with the correct srs
                converted_multilinestring = multilinestring
            else:
                # else assume the coordinates are in Espoo coordinates
                converted_multilinestring_coords = []
                for line in multilinestring:
                    converted_multilinestring_coords.append(
                        LineString(tuple((espoo_coordinates_to_gk25(point[0], point[1]) for point in line))))

                converted_multilinestring = (
                    MultiLineString((converted_multilinestring_coords), srid=3879))

            length = feat.get('PITUUS')
            if len(length) == 0:
                length = None
            maintenance_organization = '49'
            extra_fields = {
                'lighting': ESPOO_LIGHTING[feat.get('VALAISTUS')],
                'skiing_technique': HELSINKI_TECHNIQUES[feat.get('TYYLI')],
                'maintenance_group': 'kaikki',
                'maintenance_organization': maintenance_organization,
                'length': length
            }
            street_address = feat.get('street_add')
            www_url = 'http://www.espoo.fi/liikunta'
            address_zip = feat.get('zip')
            point = None
            if street_address:
                point = self.geocode_street_address(street_address, 'espoo')
            if point is None:
                point = Point(converted_multilinestring[0][0], converted_multilinestring[0][1], srid=3879)

            defaults = self.unit_defaults(
                converted_multilinestring,
                point,
                extra_fields,
                street_address, address_zip, www_url
            )
            defaults['municipality_id'] = 'espoo'
            defaults['organization_id'] = 49
            uid, did_create, unit = self._create_or_update_unit(uid, feat.get('NIMI'), defaults)
            if did_create:
                created += 1
            else:
                updated += 1
            if street_address:
                self.add_public_transportation_connection(unit, street_address, 'espoo')

        _report_counts('espoo', created, updated)

    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get('verbosity', 1))
        self.logger = logging.getLogger(__name__)
        parent = Service.objects.get(pk=33470)
        defaults = {
            'name_fi': 'Latu',
            'name_sv': 'Skidspår',
            'name_en': 'Ski track',
            'unit_count': 0,
            'parent': parent,
            'last_modified_time': timezone.now()
        }
        self.ski_service, created = Service.objects.update_or_create(pk=191, defaults=defaults)
        defaults = {
            'name_fi': 'Koiralatu',
            'name_sv': 'Hundskidspår',
            'name_en': 'Dog ski track',
            'unit_count': 0,
            'parent': parent,
            'last_modified_time': timezone.now()
        }
        self.dog_ski_service, created = Service.objects.update_or_create(pk=318, defaults=defaults)
        if self.options.get('helsinki_filename', False):
            self.import_helsinki_units(self.options['helsinki_filename'])
        if self.options.get('vantaa_filename', False):
            self.import_vantaa_units(self.options['vantaa_filename'])
        if self.options.get('espoo_filename', False):
            self.import_espoo_units(self.options['espoo_filename'])
        self.ski_service.unit_count = self.ski_service.get_unit_count()
