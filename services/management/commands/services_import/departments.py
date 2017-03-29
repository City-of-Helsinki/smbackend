from munigeo.importer.sync import ModelSyncher
from services.models import Department, Organization
from .utils import pk_get, save_translated_field


def import_departments(org_syncher=None, noop=False):
    obj_list = pk_get('department')
    syncher = ModelSyncher(Department.objects.all(), lambda obj: obj.id)
    # self.dept_syncher = syncher

    if noop:
        return

    for d in obj_list:
        obj = syncher.get(d['id'])
        if not obj:
            obj = Department(id=d['id'])
            obj._changed = True
        save_translated_field(obj, 'name', d, 'name')
        if obj.abbr != d['abbr']:
            obj._changed = True
            obj.abbr = d['abbr']

        if org_syncher:
            org_obj = org_syncher.get(d['org_id'])
        else:
            org_obj = Organization.objects.get(id=d['org_id'])
        assert org_obj

        if obj.organization_id != d['org_id']:
            obj._changed = True
            obj.organization = org_obj

        if obj._changed:
            obj.save()
        syncher.mark(obj)

    syncher.finish()
    return syncher

