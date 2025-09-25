#!/usr/bin/env python
import os
import random
import sys

import requests

values = {
    33418: {
        "ice_skating_field_condition": [
            "closed",
            "plowed",
            "frozen",
            "freezing_started",
        ]
    },
    33483: {
        "ski_trail_condition": [
            "closed",
            "good",
            "satisfactory",
            "poor",
            "snowless",
            "event",
            "littered",
            "groomed",
            "snowmaking",
        ],
        "ski_trail_maintenance": ["maintenance_finished"],
    },
}


def main(base_url):
    for service, vals in values.items():
        response = requests.get(
            base_url + f"/unit/?service={service}&only=id&page_size=1000"
        )
        assert response.status_code == 200
        fields = response.json()
        unit_ids = [u["id"] for u in fields["results"]]
        for prop, v in vals.items():
            for uid in unit_ids:
                response = requests.post(
                    base_url + "/observation/",
                    data=dict(value=random.choice(v), property=prop, unit=uid),
                    headers={"Authorization": "Token " + os.environ["API_TOKEN"]},
                )
                if response.status_code != 201:
                    print("error")  # noqa: T201
                    sys.stderr.write(response.text)
                    exit(1)


if __name__ == "__main__":
    base_url = sys.argv[1]
    main(base_url)
