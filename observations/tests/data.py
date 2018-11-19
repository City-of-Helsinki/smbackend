def observation_raw_data(observable_property_name, unit,
                         allowed_values=set()):
    if observable_property_name == 'skiing_trail_condition':
        for val in allowed_values:
            yield dict(
                unit=unit.pk,
                value=val,
                property=observable_property_name)
