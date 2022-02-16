from django.db import models


class IoTData(models.Model):
    RENT24_CARS = "R24"
    INFRAROAD_SNOW_PLOWS = "ISP"

    DATA_SOURCES = [
        (RENT24_CARS, "Rent 24 Cars"),
        (INFRAROAD_SNOW_PLOWS, "Infraroad Snow Plows"),
    ]
    created = models.DateTimeField(auto_now_add=True)
    source_name = models.CharField(
        max_length=3, choices=DATA_SOURCES, default=RENT24_CARS
    )
    data = models.JSONField(null=True)

    def get_source_names():
        return ",".join(dict(IoTData.DATA_SOURCES).keys())


