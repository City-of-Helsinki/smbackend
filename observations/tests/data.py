
def observation_raw_data(observable_property_type, unit,
                           allowed_values=set()):

    dt = d.datetime(year=2016, month=8, day=20, hour=9, minute=21, second=5)
    otype = observable_property.observation_type
    if otype == 'categorical':
        return dict(
            time=dt,
            unit=unit.pk,
            value=1,
            property=observable_property.pk
        )
