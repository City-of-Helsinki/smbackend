

OBSERVABLE_PROPERTY_IDENTICAL_FIELDS = [
    # These fields should be identical in
    # the original object and its JSON (dict) representation.
    'id', 'name', 'measurement_unit'
]

OBSERVATION_CLASS_KEYS = {
    'observations.CategoricalObservation': 'categorical',
    'observations.ContinuousObservation': 'continuous',
    'observations.DescriptiveObservation': 'descriptive'
}

def match_observable_property_object_to_dict(obj, dict):
    for f in OBSERVABLE_PROPERTY_IDENTICAL_FIELDS:
        obj_value = getattr(obj, f)
        assert dict[f] == obj_value
    a = dict['observation_type']
    b = OBSERVATION_CLASS_KEYS[obj.observation_type]
    assert a == b, '%s does not equal %s' % (a,b)
