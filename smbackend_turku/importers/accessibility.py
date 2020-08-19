from munigeo.importer.sync import ModelSyncher

from services.models import (
    AccessibilityVariable,
    UnitAccessibilityProperty,
    UnitIdentifier,
)
from smbackend_turku.importers.utils import (
    get_ar_resource,
    get_ar_servicepoint_accessibility_resource,
    get_ar_servicepoint_resource,
)


class AccessibilityImporter:
    def __init__(self, logger):
        self.logger = logger
        self.__accessibility_variable_cache = {}

    def import_accessibility(self):
        self._import_accessibility_variables()
        self._update_unit_accessibility_info()
        self._import_unit_accessibility_properties()

    @property
    def _accessibility_variables(self):
        if not self.__accessibility_variable_cache:
            self.__accessibility_variable_cache = {
                variable.id: variable
                for variable in AccessibilityVariable.objects.all()
            }

        return self.__accessibility_variable_cache

    def _import_accessibility_variables(self):
        num_of_imports = 0

        variables = get_ar_resource("accessibility/variables")
        for variable in variables:
            variable_name = variable.get("variableName")
            variable_id = variable.get("variableId")
            if not (variable_name and variable_id):
                continue
            (
                accessibility_variable,
                created,
            ) = AccessibilityVariable.objects.update_or_create(
                id=variable_id, defaults={"name": variable_name}
            )
            self.__accessibility_variable_cache[variable_id] = accessibility_variable
            if created:
                num_of_imports += 1

        self.logger.info("Imported {} accessibility variables.".format(num_of_imports))

    def _update_unit_accessibility_info(self):
        num_of_updated_units = 0

        service_points = get_ar_servicepoint_resource()
        for service_point in service_points:
            ptv_id = service_point.get("servicePointId")
            if not ptv_id:
                continue

            try:
                unit_identifier = UnitIdentifier.objects.get(
                    namespace="ptv", value=ptv_id
                )
                unit = unit_identifier.unit
            except UnitIdentifier.DoesNotExist:
                continue

            changed = self._set_unit_accesibility_properties(unit, service_point)
            if changed:
                unit.save()
                num_of_updated_units += 1

        self.logger.info("Updated {} units.".format(num_of_updated_units))

    def _import_unit_accessibility_properties(self):
        property_syncher = ModelSyncher(
            UnitAccessibilityProperty.objects.all(), lambda obj: obj.id
        )
        num_of_imports = 0

        # For caching unit ids that are not present in the database
        unit_skip_list = set([])

        accessibility_properties = get_ar_servicepoint_accessibility_resource(
            "properties"
        )
        for accessibility_property in accessibility_properties:
            # Make sure that we have all the necessary property attributes
            ptv_id = accessibility_property.get("servicePointId")
            accessibility_variable_id = accessibility_property.get("variableId")
            accessibility_variable_value = accessibility_property.get("value")
            if not (
                ptv_id and accessibility_variable_id and accessibility_variable_value
            ):
                continue

            # No need to check further if the unit has already been marked as non-existing
            if ptv_id in unit_skip_list:
                continue

            # Make sure that the unit exists
            try:
                # TODO: Optimize this if it gets too slow
                # One way is to get all unit ids in one go and make a lookup table
                unit_identifier = UnitIdentifier.objects.get(
                    namespace="ptv", value=ptv_id
                )
                unit = unit_identifier.unit
            except UnitIdentifier.DoesNotExist:
                self.logger.info("Unit {} does not exist, skipping".format(ptv_id))
                unit_skip_list.add(ptv_id)
                continue

            # Make sure that the variable exists
            if accessibility_variable_id not in self._accessibility_variables:
                self.logger.info("No variable {}, skipping".format(ptv_id))
                continue

            # Create or update the property including its associated value
            uap, created = UnitAccessibilityProperty.objects.update_or_create(
                unit=unit,
                variable_id=accessibility_variable_id,
                defaults={"value": accessibility_variable_value},
            )

            # If an entry was updated
            if not created:
                # Mark it as synced
                sync_uap = property_syncher.get(uap.id)
                if sync_uap:
                    property_syncher.mark(sync_uap)

            if created:
                num_of_imports += 1

        property_syncher.finish()
        self.logger.info("Imported {} accessibility properties.".format(num_of_imports))

    def _set_unit_accesibility_properties(self, unit, accessiblity_entry):
        accessibility_properties = [
            "accessibility_phone",
            "accessibility_email",
            "accessibility_www",
        ]
        changed = False

        for accessibility_property in accessibility_properties:
            entry_value = accessiblity_entry.get(accessibility_property)
            unit_value = getattr(unit, accessibility_property)
            if entry_value == unit_value:
                continue
            setattr(unit, accessibility_property, entry_value)
            changed = True

        return changed


def import_accessibility(**kwargs):
    importer = AccessibilityImporter(**kwargs)
    importer.import_accessibility()
