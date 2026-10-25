"""Sample API payload used across tests.

Covers the tricky cases: a split staffed+self-service day (Borensbergs), a
self-service-only entry, a duplicate-listed branch with a leading space
(Finspångs huvudbibliotek), and a branch that only appears on day two
(Mjölby) so the branch-name union is exercised.
"""

from custom_components.gotabiblioteken.data import ApiPayload

SAMPLE_PAYLOAD: ApiPayload = {
    "dates": [
        {
            "date": "2026-10-20",
            "branches": [
                {
                    "branchName": "Motala bibliotek",
                    "openingHours": [
                        {
                            "serviceType": "Staffed",
                            "info": None,
                            "from": "10:00",
                            "to": "19:00",
                            "openingHoursType": "Regular",
                        }
                    ],
                },
                {
                    "branchName": "Borensbergs bibliotek",
                    "openingHours": [
                        {
                            "serviceType": "Staffed",
                            "info": None,
                            "from": "09:00",
                            "to": "14:00",
                            "openingHoursType": "Regular",
                        },
                        {
                            "serviceType": "SelfService",
                            "info": "Meröppet",
                            "from": "14:00",
                            "to": "21:00",
                            "openingHoursType": "Regular",
                        },
                    ],
                },
                {
                    "branchName": " Finspångs huvudbibliotek",
                    "openingHours": [
                        {
                            "serviceType": "Staffed",
                            "info": None,
                            "from": "12:00",
                            "to": "18:00",
                            "openingHoursType": "Regular",
                        }
                    ],
                },
                {
                    "branchName": "Finspångs huvudbibliotek",
                    "openingHours": [
                        {
                            "serviceType": "Staffed",
                            "info": None,
                            "from": "12:00",
                            "to": "18:00",
                            "openingHoursType": "Regular",
                        },
                        {
                            "serviceType": "SelfService",
                            "info": "Meröppet",
                            "from": "09:00",
                            "to": "12:00",
                            "openingHoursType": "Regular",
                        },
                    ],
                },
            ],
        },
        {
            "date": "2026-10-21",
            "branches": [
                {
                    "branchName": "Mjölby bibliotek",
                    "openingHours": [
                        {
                            "serviceType": "Staffed",
                            "info": None,
                            "from": "08:00",
                            "to": "17:00",
                            "openingHoursType": "Regular",
                        }
                    ],
                }
            ],
        },
    ]
}
