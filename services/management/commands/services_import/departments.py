from munigeo.importer.sync import ModelSyncher
from munigeo.models import Municipality

from services.models import Department

from .utils import pk_get, save_translated_field


def import_departments(noop=False, logger=None, fetch_resource=pk_get):
    obj_list = fetch_resource('department')
    syncher = ModelSyncher(Department.objects.all(), lambda obj: str(obj.uuid))
    # self.dept_syncher = syncher
    if noop:
        return syncher

    for d in sorted(obj_list, key=lambda x: x['hierarchy_level']):
        obj = syncher.get(d['id'])
        obj_has_changed = False
        if not obj:
            obj = Department(uuid=d['id'])
            obj_has_changed = True

        fields = ('phone', 'address_zip', 'oid', 'organization_type',
                  'business_id')
        fields_that_need_translation = ('name', 'abbr', 'street_address', 'address_city', 'address_postal_full',
                                        'www')

        obj.uuid = d['id']

        for field in fields:
            if d.get(field):
                if d[field] != getattr(obj, field):
                    obj_has_changed = True
                    setattr(obj, field, d.get(field))

        parent_id = d.get('parent_id')
        if parent_id != obj.parent_id:
            obj_has_changed = True
            if parent_id is None:
                obj.parent_id = None
            else:
                try:
                    parent = Department.objects.get(uuid=parent_id)
                    obj.parent_id = parent.id
                except Department.DoesNotExist:
                    logger and logger.error(
                        "Department import: no parent with uuid {} found for {}".format(
                            parent_id, d['id'])
                    )

        for field in fields_that_need_translation:
            if save_translated_field(obj, field, d, field):
                obj_has_changed = True

        muni_code = d.get('municipality_code')
        if muni_code is None:
            municipality = None
        if muni_code is not None:
            try:
                municipality = Municipality.objects.get(division__origin_id=str(muni_code))
            except Municipality.DoesNotExist:
                logger and logger.error(
                    "No municipality with code {} for department {}".format(
                        muni_code, d['id']))
        if obj.municipality != municipality:
            obj.municipality = municipality
            obj_has_changed = True

        if obj_has_changed:
            obj.save()
        syncher.mark(obj)

    syncher.finish()
    return syncher
