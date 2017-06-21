from munigeo.importer.sync import ModelSyncher
from services.models import Department, Organization
from .utils import pk_get, save_translated_field


def import_departments(org_syncher=None, noop=False, logger=None, fetch_resource=pk_get):
    obj_list = fetch_resource('department')
    syncher = ModelSyncher(Department.objects.all(), lambda obj: str(obj.uuid))
    # self.dept_syncher = syncher
    if noop:
        return syncher

    for d in sorted(obj_list, key=lambda x: x['hierarchy_level']):
        # if int(d['hierarchy_level']) == 0:
        #     logger and logger.info(
        #         "Department import: %s (%s) hierarchy_level is 0, thus is a Main Organization, skipping."
        #         % (d['name_fi'], d['id']))
        #     # TODO why this?
        #     continue

        obj = syncher.get(d['id'])
        obj_has_changed = False
        if not obj:
            obj = Department(uuid=d['id'])
            obj_has_changed = True

        fields = ('phone', 'address_zip', 'hierarchy_level', 'oid', 'organization_type',
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

        if org_syncher:
            org_obj = org_syncher.get(d['org_id'])
        else:
            org_obj = Organization.objects.get(uuid=d['org_id'])

        assert org_obj, "Organization '%s' for department '%s' does not exist - bailing out" % (d['org_id'], obj)

        if obj.organization_id != d['org_id']:
            obj_has_changed = True
            obj.organization = org_obj

        if obj_has_changed:
            obj.save()
        syncher.mark(obj)

    syncher.finish()
    return syncher
