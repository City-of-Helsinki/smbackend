import pprint
from munigeo.importer.sync import ModelSyncher
from services.models import Organization
from .utils import pk_get, save_translated_field


def import_organizations(org_syncher=None, noop=False, logger=None, fetch_resource=pk_get):
    obj_list = fetch_resource('organization')
    syncher = ModelSyncher(Organization.objects.all(), lambda obj: str(obj.uuid))
    # self.dept_syncher = syncher
    if noop:
        return syncher

    for d in obj_list:
        # pprint.pprint(d)

        obj = syncher.get(d['id'])
        obj_has_changed = False
        if not obj:
            obj = Organization(uuid=d['id'])
            obj_has_changed = True

        fields = ('phone', 'address_zip', 'data_source_url', 'municipality_code',
                  'oid', 'organization_type', 'business_id')
        fields_that_need_translation = ('name', 'abbr', 'street_address', 'address_city',
                                        'address_postal_full', 'www')

        obj.uuid = d['id']

        for field in fields:
            if d.get(field):
                if d[field] != getattr(obj, field):
                    obj_has_changed = True
                    setattr(obj, field, d.get(field))

        for field in fields_that_need_translation:
            if save_translated_field(obj, field, d, field):
                obj_has_changed = True

        if obj_has_changed:
            obj.save()
        syncher.mark(obj)

    syncher.finish()
    return syncher

