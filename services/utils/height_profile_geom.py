def multilinestring_to_linestring_features(coords):
    if coords is None:
        return None

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": line},
                "properties": {
                    "attributeType": "flat"
                },  # TODO: Add support for other types
            }
            for line in coords
        ],
        "properties": {
            "summary": "Height",
            "label": "Height profile",
            "label_fi": "Korkeusprofiili",
            "label_sv": "Höjdprofil",
        },
    }
