import uuid
from datetime import datetime

from django import db
from django.contrib.gis.geos import Point
from munigeo.importer.sync import ModelSyncher
from munigeo.models import Municipality

from ptv.models import ServicePTVIdentifier, UnitPTVIdentifier
from ptv.utils import create_available_id, get_ptv_resource, UTC_TIMEZONE
from services.models import Unit, UnitConnection, UnitIdentifier

PHONE_OR_EMAIL_SECTION_TYPE = 1
OPENING_HOURS_SECTION_TYPE = 5

WEEKDAYS = {
    "Monday": {"fi": "Ma", "sv": "Mån", "en": "Mon"},
    "Tuesday": {"fi": "Ti", "sv": "Tis", "en": "Tue"},
    "Wednesday": {"fi": "Ke", "sv": "Ons", "en": "Wed"},
    "Thursday": {"fi": "To", "sv": "Tors", "en": "Thu"},
    "Friday": {"fi": "Pe", "sv": "Fre", "en": "Fri"},
    "Saturday": {"fi": "La", "sv": "Lör", "en": "Sat"},
    "Sunday": {"fi": "Su", "sv": "Sön", "en": "Sun"},
}


class UnitPTVImporter:
    def __init__(self, area_code):
        self.are_code = area_code
        self.unit_syncher = ModelSyncher(
            Unit.objects.filter(
                ptv_id__isnull=False, ptv_id__source_municipality=self.are_code
            ),
            lambda obj: obj.id,
        )
        self.unit_id_syncher = ModelSyncher(
            UnitPTVIdentifier.objects.all(), lambda obj: obj.id
        )
        self.service_id_syncher = ModelSyncher(
            ServicePTVIdentifier.objects.all(), lambda obj: obj.id
        )

    @db.transaction.atomic
    def import_units(self):
        data = get_ptv_resource(self.are_code)
        page_count = data["pageCount"]
        for page in range(1, page_count + 1):
            if page > 1:
                data = get_ptv_resource(self.are_code, page=page)
            self._import_units(data)

        self.unit_syncher.finish()

    def _import_units(self, data):
        id_counter = 1
        for item in data["itemList"]:
            # Import only the channels that have a location
            if item["serviceChannelType"] == "ServiceLocation":
                self._handle_unit(item, id_counter)
                id_counter += 1

    def _handle_unit(self, unit_data, id_counter):
        uuid_id = uuid.UUID(unit_data["id"])

        # Skip the import if unit has been imported from another source
        if Unit.objects.filter(
            identifiers__value=uuid_id, identifiers__namespace="ptv"
        ).exclude(data_source="PTV"):
            return

        ptv_id_obj = self.unit_id_syncher.get(uuid_id)
        if not ptv_id_obj:
            ptv_id_obj = UnitPTVIdentifier(
                id=uuid_id, source_municipality=self.are_code
            )
            ptv_id_obj._changed = True

        if ptv_id_obj.unit:
            unit_id = ptv_id_obj.unit.id
        else:
            # Create an id by getting next available id since AutoField is not in use.
            unit_id = create_available_id(Unit, id_counter)

        unit_obj = self.unit_syncher.get(unit_id)
        if not unit_obj:
            unit_obj = Unit(id=unit_id)
            unit_obj._changed = True
            ptv_id_obj.unit = unit_obj

        if not ptv_id_obj.source_municipality:
            ptv_id_obj.source_municipality = self.are_code
            ptv_id_obj._changed = True

        self._save_object(ptv_id_obj)
        self._handle_fields(unit_obj, unit_data)
        self._handle_service_ids(unit_obj, unit_data)
        self._save_object(unit_obj)
        self.unit_syncher.mark(unit_obj)

    def _handle_fields(self, unit_obj, unit_data):
        self._handle_name_and_description(unit_obj, unit_data)
        self._handle_location(unit_obj, unit_data)
        self._handle_extra_info(unit_obj, unit_data)
        self._save_object(unit_obj)
        self._handle_ptv_id(unit_obj, unit_data)
        self._handle_opening_hours(unit_obj, unit_data)
        self._handle_email_and_phone_numbers(unit_obj, unit_data)
        unit_obj.data_source = "PTV"

    def _handle_name_and_description(self, unit_obj, unit_data):
        for name in unit_data["serviceChannelNames"]:
            if name.get("type") == "Name":
                self._handle_translation(unit_obj, name, "name")

        for description in unit_data["serviceChannelDescriptions"]:
            self._handle_translation(unit_obj, description, "description")

    def _handle_location(self, unit_obj, unit_data):
        if unit_data["addresses"]:
            address = unit_data["addresses"][0].get("streetAddress")
            if address:
                # Coordinates
                latitude = address.get("latitude")
                longitude = address.get("longitude")
                if latitude and longitude:
                    point = Point(float(longitude), float(latitude))
                    unit_obj.location = point

                # Address
                unit_obj.address_zip = address["postalCode"]
                for street in address.get("street"):
                    street_address = "{} {}".format(
                        street.get("value"), address.get("streetNumber")
                    )
                    self._handle_translation(
                        unit_obj, street, "street_address", street_address
                    )

                    post_office = address["postOffice"][0]["value"]
                    for po in address["postOffice"]:
                        if po["language"] == street.get("language"):
                            post_office = po["value"]

                    address_postal_full = "{} {} {}".format(
                        street_address, unit_obj.address_zip, post_office
                    )
                    self._handle_translation(
                        unit_obj,
                        street,
                        "address_postal_full",
                        address_postal_full,
                    )

                # Municipality
                municipality_name = next(
                    item.get("value")
                    for item in address["municipality"].get("name")
                    if item["language"] == "fi"
                )
                try:
                    municipality = Municipality.objects.get(name=municipality_name)
                except Municipality.DoesNotExist:
                    municipality = None
                unit_obj.municipality = municipality

    def _handle_extra_info(self, unit_obj, unit_data):
        emails = unit_data["emails"]
        if emails:
            unit_obj.email = emails[0].get("value")

        for web_page in unit_data.get("webPages", []):
            value = web_page.get("url")
            self._handle_translation(unit_obj, web_page, "www", value)

    def _handle_ptv_id(self, unit_obj, unit_data):
        ptv_id = unit_data.get("id")
        if ptv_id:
            created, _ = UnitIdentifier.objects.get_or_create(
                namespace="ptv", value=ptv_id, unit=unit_obj
            )
            if created:
                unit_obj._changed = True
        else:
            num_of_deleted, _ = UnitIdentifier.objects.filter(
                namespace="ptv", unit=unit_obj
            ).delete()
            if num_of_deleted:
                unit_obj._changed = True

    def _handle_opening_hours(self, obj, unit_data):
        obj.connections.filter(section_type=OPENING_HOURS_SECTION_TYPE).delete()
        service_hours = unit_data.get("serviceHours", [])
        for service_hour in service_hours:
            index = 0
            names = {}
            opening_hours = service_hour.get("openingHour")
            for language in ["fi", "sv", "en"]:
                opening_hour_data = []
                for opening_hour in opening_hours:
                    week_day = opening_hour["dayFrom"]
                    opens = opening_hour["from"][
                        :-3
                    ]  # Strip the extra zeros away from eg. "08:00:00"
                    closes = opening_hour["to"][:-3]

                    if week_day:
                        opening_hour_data.append(
                            "{} {}-{}".format(
                                WEEKDAYS[week_day][language], opens, closes
                            )
                        )

                names["name_{}".format(language)] = "{}".format(
                    "\n".join(opening_hour_data)
                )

                additional_info = []
                for info in service_hour.get("additionalInformation", []):
                    lang = info.get("language")
                    if lang == language and info.get("value"):
                        additional_info.append(info.get("value"))

                if additional_info:
                    names["name_{}".format(language)] = "\n".join(
                        ("\n".join(additional_info), names["name_{}".format(language)])
                    )

            UnitConnection.objects.create(
                unit=obj, section_type=OPENING_HOURS_SECTION_TYPE, order=index, **names
            )
            index += 1

    def _handle_email_and_phone_numbers(self, unit_obj, unit_data):
        UnitConnection.objects.filter(
            unit=unit_obj, section_type=PHONE_OR_EMAIL_SECTION_TYPE
        ).delete()
        index = 0
        emails = unit_data.get("emails", [])
        for email in emails:
            UnitConnection.objects.get_or_create(
                unit=unit_obj,
                section_type=PHONE_OR_EMAIL_SECTION_TYPE,
                email=email.get("value"),
                name_fi="Sähköposti",
                name_sv="E-post",
                name_en="Email",
                order=index,
            )
            index += 1

        numbers = unit_data.get("phoneNumbers", [])
        for number in numbers:            
            prefix_number = number.get("prefixNumber", "")
            postfix_number = number.get("number", "")
            if not prefix_number:
                prefix_number = ""
            if not postfix_number:
                postfix_number = ""
            phone_number = prefix_number + postfix_number
            contact_info = number.get("additionalInformation")
            name = {}
            if contact_info:
                obj_key = "{}_{}".format("name", number.get("language", "fi"))
                name[obj_key] = contact_info
                UnitConnection.objects.get_or_create(
                    unit=unit_obj,
                    section_type=PHONE_OR_EMAIL_SECTION_TYPE,
                    phone=phone_number,
                    order=index,
                    **name
                )
                index += 1
            else:
                unit_obj.phone = phone_number

    def _handle_translation(self, obj, data, field_name, value=None):
        lang = data.get("language")
        if not value:
            value = data.get("value")
        obj_key = "{}_{}".format(field_name, lang)
        setattr(obj, obj_key, value)

    def _handle_service_ids(self, unit_obj, unit_data):
        unit_obj.services.clear()
        for service in unit_data["services"]:
            uuid_id = uuid.UUID(service.get("service").get("id"))
            id_obj = self.service_id_syncher.get(uuid_id)
            if not id_obj:
                id_obj = ServicePTVIdentifier(id=uuid_id)
                id_obj._changed = True
            self._save_object(id_obj)

    def _save_object(self, obj):
        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
