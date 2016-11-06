import datetime as d

def observation_raw_data(observable_property_name, unit,
                           allowed_values=set()):

    dt = d.datetime(year=2016, month=8, day=20, hour=9, minute=21, second=5)
    if observable_property_name == 'skiing_track_condition':
        return dict(
            time=dt,
            unit=unit.pk,
            identifier='good',
            property=observable_property_name
        )
