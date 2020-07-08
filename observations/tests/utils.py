OBSERVABLE_PROPERTY_IDENTICAL_FIELDS = [
    # These fields should be identical in
    # the original object and its JSON (dict) representation.
    "id",
    "measurement_unit",
]

OBSERVABLE_PROPERTY_TRANSLATED_FIELDS = ["name"]

OBSERVATION_CLASS_KEYS = {
    "observations.CategoricalObservation": "categorical",
    "observations.ContinuousObservation": "continuous",
    "observations.DescriptiveObservation": "descriptive",
}


def match_observable_property_object_to_dict(obj, data):
    for f in OBSERVABLE_PROPERTY_IDENTICAL_FIELDS:
        obj_value = getattr(obj, f)
        assert data[f] == obj_value
    for f in OBSERVABLE_PROPERTY_TRANSLATED_FIELDS:
        obj_value = getattr(obj, f)
        assert data[f]["fi"] == obj_value

    a = data["observation_type"]
    b = OBSERVATION_CLASS_KEYS[obj.observation_type]
    assert a == b, "%s does not equal %s" % (a, b)
