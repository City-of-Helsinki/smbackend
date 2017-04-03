from django.db import models
from .unit import Unit

SECTION_TYPES = (
    (1, 'PHONE_OR_EMAIL'),
    (2, 'LINK'),
    (3, 'TOPICAL'),
    (4, 'OTHER_INFO'),
    (5, 'OPENING_HOURS'),
    (6, 'SOCIAL_MEDIA_LINK'),
    (7, 'OTHER_ADDRESS'),
)


class UnitConnection(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='connections')
    name = models.CharField(max_length=400)
    www = models.URLField(null=True, max_length=400)
    section_type = models.PositiveSmallIntegerField(choices=SECTION_TYPES, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone = models.CharField(max_length=50, null=True)
    contact_person = models.CharField(max_length=80, null=True)

    # section = models.CharField(max_length=20)
    # phone_mobile = models.CharField(max_length=50, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']


    # {'contact_person': 'Miia Kovalainen',
    # 'email': 'miia.kovalainen@hel.fi',
    # 'name_en': 'Head of day care centre',
    # 'name_fi': 'Päiväkodinjohtaja',
    # 'name_sv': 'Daghemsföreståndare',
    # 'phone': '09 310 41571',
    # 'section_type': 'PHONE_OR_EMAIL',
    # 'unit_id': 1},

    # {'name_en': 'Application for day care',
    # 'name_fi': 'Täytä päivähoitohakemus',
    # 'name_sv': 'Ansökan om barndagvård',
    # 'section_type': 'LINK',
    # 'unit_id': 1,
    # 'www_en': 'http://www.hel.fi/www/helsinki/en/day-care-education/day-care/options/applying',
    # 'www_fi': 'http://www.hel.fi/www/Helsinki/fi/paivahoito-ja-koulutus/paivahoito/paivakotihoito/hakeminen',
    # 'www_sv': 'http://www.hel.fi/www/helsinki/sv/dagvard-och-utbildning/dagvord/ansokan/ansokan-dagvard'}

