import pytz
import requests
from django.conf import settings
from django.db.models import Max

PTV_BASE_URL = "https://api.palvelutietovaranto.suomi.fi/api/v11/"

UTC_TIMEZONE = pytz.timezone("UTC")


def get_ptv_resource(area_code, resource_name=None, page=1):
    if resource_name == "service":
        endpoint = "Service/list/area/Municipality/code/"
    else:
        endpoint = "ServiceChannel/list/area/Municipality/code/"
    url = "{}{}{}?page={}".format(PTV_BASE_URL, endpoint, area_code, page)
    print("CALLING URL >>> ", url)
    resp = requests.get(url)
    assert resp.status_code == 200, "status code {}".format(resp.status_code)
    return resp.json()


def create_available_id(model, increment=0):
    """
    Create an id by getting next available id since AutoField is not in use.
    "Reserve" first 10 000 id's for Turku data, so they can be kept the same as they are in the original source.
    Not a pretty solution so probably need to TODO: rethink the id system when more than one data source is in use.
    """
    new_id = (model.objects.aggregate(Max("id"))["id__max"] or 0) + increment
    if "smbackend_turku" in settings.INSTALLED_APPS:
        buffer = settings.PTV_ID_OFFSET
        if new_id < buffer:
            new_id += buffer
    return new_id


TKU_PTV_NODE_MAPPING = {
    **dict.fromkeys(
        [
            "Maankäyttö",
            "Kaavoitus",
            "Tontit",
            "Rakennettu ympäristö",
            "Paikkatieto",
            "Kartat ja karttapalvelut",
            "Paikkatietopalvelut",
            "Vakuutukset",
        ],
        ["Asuminen ja ympäristö"],
    ),
    "Toimialakohtaiset luvat ja velvoitteet": [
        "Asuminen ja ympäristö",
        "Palvelut yrityksille",
    ],
    **dict.fromkeys(
        [
            "Kiinteistöt",
            "Rakentaminen",
            "Korjaus- ja energia-avustukset",
            "Maankäyttö, kaavoitus ja tontit",
        ],
        [
            "Kaavoitus, kiinteistöt ja rakentaminen",
        ],
    ),
    "Rakennusperintö ja kulttuuriympäristöt": [
        "Kaavoitus, kiinteistöt ja rakentaminen",
        "Ympäristö",
        "Kulttuuri",
    ],
    **dict.fromkeys(
        ["Vuokra-asuminen", "Omistusasumien", "Osaomistus- ja asumisoikeusasuminen"],
        ["Asuminen"],
    ),
    **dict.fromkeys(
        ["Jätehuolto", "Vesihuolto", "Energiahuolto"], ["Asuminen", "Ympäristö"]
    ),
    "Kotitalous työnantajana": ["Asuminen", "Tuet ja etuudet", "Palvelut yrityksille"],
    **dict.fromkeys(
        ["Omaisuuden verotus", "Yksityinen talous ja rahoitus", "Paluumuutto"],
        ["Asuminen", "Vaikuttaminen ja hallinto"],
    ),
    **dict.fromkeys(
        [
            "Pysäköinti",
            "Joukkoliikenne",
            "Ajoneuvojen verotus",
            "Ajoneuvot ja rekisteröinti tieliikenteessä",
            "Ajo-opetus ja ajoluvat tieliikenteessä",
            "Liikenneturvallisuus ja liikennesäännöt tieliikenteessä",
            "Ammattiliikenne tielii-kenteessä",
            "Tienpito",
            "Vesiliikenne",
            "Ilmailu",
        ],
        ["Liikenne"],
    ),
    "Matkailu": ["Liikenne", "Työ- ja yrityspalvelut", "Nähtävyydet ja matkailuinfo"],
    **dict.fromkeys(
        ["Matkailu EU-alueella", "Matkailu EU-alueen ulkopuolella"],
        [
            "Liikenne",
            "Nähtävyydet ja matkailuinfo",
            "Vaikuttaminen ja hallinto",
        ],
    ),
    **dict.fromkeys(
        [
            "Palo- ja pelastustoiminta",
            "Väestönsuojelu",
            "Hätänumerot ja onnettomuustilanteet",
            "Rikosten ilmoittaminen",
            "Säteilyturvallisuus",
        ],
        ["Turvallisuus"],
    ),
    "Tietosuoja ja henkilötiedot": [
        "Turvallisuus",
        "Aineisto- ja tietopalvelut",
        "Vaikuttaminen ja hallinto",
    ],
    **dict.fromkeys(
        ["Lait ja asetukset", "Laillisuusvalvonta"],
        [
            "Turvallisuus",
            "Oikeudelliset palvelut",
            "Vaikuttaminen ja hallinto",
        ],
    ),
    **dict.fromkeys(
        ["Syyttäjälaitos", "Tuomioistuimet", "Maanpuolustus", "Rajavalvonta"],
        ["Turvallisuus", "Vaikuttaminen ja hallinto"],
    ),
    "Järjestyksen valvonta ja poliisin myöntämät luvat": [
        "Turvallisuus",
        "Työ- ja yrityspalvelut",
    ],
    "Tilaisuuksien järjestäminen": [
        "Turvallisuus",
        "Työ- ja yrityspalvelut",
        "Tontit ja toimitilat",
        "Vapaa-aika",
    ],
    **dict.fromkeys(
        [
            "Ympäristön- ja luonnonsuojelu",
            "Ympäristövalvonta ja -terveydenhuolto",
            "Luonnonvarat, eläimet ja kasvit",
        ],
        ["Ympäristö"],
    ),
    **dict.fromkeys(
        [
            "Ympäristöilmoitukset ja luvat",
            "Kasvintuotanto",
            "Tuotantoeläimet",
            "Metsä-, vesi- ja mineraalivarat",
        ],
        ["Ympäristö", "Työ- ja yrityspalvelut"],
    ),
    "Luonnonvaraiset kasvit ja eläimet": ["Ympäristö", "Puistot"],
    "Elintarviketurvallisuus": ["Ympäristö", "Palvelut yrityksille"],
    **dict.fromkeys(
        ["Koulutus", "Perusopetus", "Lukiokoulutus"], ["Päivähoito ja koulutus"]
    ),
    "Lasten päivähoito": ["Päivähoito ja esiopetus", "Leikkipuistot"],
    "Esiopetus": ["Päivähoito ja esiopetus"],
    "Koulu- ja opiskelijahuollon sosiaalipalvelut": [
        "Lukiokoulutus",
        "Perusopetus",
        "Ammatillinen koulutus",
        "Muu sosiaalihuolto",
    ],
    "Koulu- ja opiskelijaterveydenhuolto": [
        "Lukiokoulutus",
        "Perusopetus",
        "Ammatillinen koulutus",
    ],
    "Ammatinvalinta ja opintojen ohjaus": [
        "Lukiokoulutus",
        "Perusopetus",
        "Ammatillinen koulutus",
    ],
    "Koulutukseen hakeminen": [
        "Lukiokoulutus",
        "Ammatillinen koulutus",
        "Aikuiskoulutus",
    ],
    **dict.fromkeys(
        [
            "Aamu- ja iltapäiväkerhotoiminta",
            "Vapaa sivistystyö ja taidekasvatus",
            "Uskonnot ja elämänkatsomukset",
        ],
        ["Perusopetus"],
    ),
    "Opiskelu ulkomailla": [
        "Ammattikorkeakoulut ja yliopistot",
        "Ammatillinen koulutus",
    ],
    **dict.fromkeys(
        ["Korkeakoulutus", "Tiede ja tutkimus"], ["Ammattikorkeakoulut ja yliopistot"]
    ),
    "Immateriaalioikeudet": [
        "Ammattikorkeakoulut ja yliopistot",
        "Palvelut yrityksille",
    ],
    "Kielikurssit": ["Ammattikorkeakoulut ja yliopistot", "Aikuiskoulutus"],
    "Maahanmuuttajan työskentely ja opiskelu": [
        "Ammattikorkeakoulut ja yliopistot",
        "Ammatillinen koulutus",
        "Aikuiskoulutus",
        "Työllisyyspalvelut",
        "Vaikuttaminen ja hallinto",
    ],
    "Toisen asteen ammatillinen koulutus": ["Ammatillinen koulutus"],
    "Oppisopimus": ["Ammatillinen koulutus", "Palvelut yrityksille"],
    "Aikuis- ja täydennyskoulutus": ["Aikuiskoulutus"],
    "Opintojen tukeminen": ["Aikuiskoulutus", "Tuet ja etuudet"],
    "Ammatinvalinta ja urasuunnittelu": ["Aikuiskoulutus", "Työllisyyspalvelut"],
    "Henkilöstön kehittäminen": [
        "Aikuiskoulutus",
        "Työllisyyspalvelut",
        "Palvelut yrityksille",
    ],
    **dict.fromkeys(
        ["Terveyspalvelut", "Sosiaalipalvelujen neuvonta- ja ohjauspalvelu"],
        ["Sosiaali- ja terveyspalvelut"],
    ),
    "Hyvinvointipalvelujen tukipalvelut": [
        "Sosiaali- ja terveyspalvelut",
        "Terveyspalvelut",
    ],
    **dict.fromkeys(
        [
            "Sosiaalipalvelujen neuvonta- ja ohjauspalvelut",
            "Sosiaalipalvelujen vertais- ja vapaaehtoistoiminta",
        ],
        ["Sosiaalipalvelut"],
    ),
    **dict.fromkeys(
        [
            "Perheiden palvelut",
            "Lapsiperheiden sosiaalipalvelut",
            "Lapsen saaminen",
            "Isyyden vahvistaminen",
            "Isyyden vahvistaminen",
            "Elatusapu",
            "Parisuhde",
        ],
        ["Lapsiperheen tuet"],
    ),
    "Perhehoito": ["Lastensuojelu"],
    "Sosiaalipalvelujen oheis- ja tukipalvelut": [
        "Muu sosiaalihuolto",
        "Tuet ja etuudet",
    ],
    **dict.fromkeys(
        [
            "Asumispalvelut",
            "Kotihoito ja kotipalvelut",
            "Kehitysvammahuolto",
            "Kotouttaminen",
        ],
        ["Muu sosiaalihuolto"],
    ),
    "Asioinnin tukipalvelut": [
        "Muu sosiaalihuolto",
        "Oikeudelliset palvelut",
        "Vaikuttaminen ja hallinto",
    ],
    **dict.fromkeys(
        [
            "Asumisen tuet",
            "Henkilökohtaisen avustajan palvelut",
            "Toimeentulotuki",
            "Eläkkeet",
            "Kansaneläke",
            "Työeläkkeet",
        ],
        ["Tuet ja etuudet"],
    ),
    "Työttömän tuet ja etuudet": ["Tuet ja etuudet", "Työllisyyden hoitaminen"],
    "Työkyvyttömyyseläke": ["Tuet ja etuudet", "Kuntoutumispalvelut"],
    **dict.fromkeys(
        [
            "Suomalaisen eläketurva ulkomailla",
            "Suomessa pysyvästi asuvan ulkomaalaisen eläketurva Suomessa",
        ],
        [
            "Tuet ja etuudet",
            "Vaikuttaminen ja hallinto",
        ],
    ),
    "Henkilön talous- ja velkaneuvonta": ["Tuet ja etuudet", "Oikeudelliset palvelut"],
    **dict.fromkeys(
        [
            "Oikeusturva",
            "Perheasioiden sovittelu ja perheoikeus",
            "Oikeusapu",
            "Rangaistukset",
        ],
        ["Oikeudelliset palvelut"],
    ),
    "Edunvalvonta": ["Oikeudelliset palvelut", "Vaikuttaminen ja hallinto"],
    **dict.fromkeys(
        ["Lainat ja luottotiedot", "Ulosotto"],
        ["Oikeudelliset palvelut", "Palvelut yrityksille"],
    ),
    "Talletusten ja sijoitusten suoja": [
        "Oikeudelliset palvelut",
        "Vaikuttaminen ja hallinto",
    ],
    "Työ ja työttömyys": ["Työllisyyden hoitaminen", "Työ- ja yrityspalvelut"],
    **dict.fromkeys(
        ["Työllistyjän taloudellinen tukeminen", "Työttömien järjestöt ja vertaistuki"],
        ["Työllisyyden hoitaminen"],
    ),
    "Tuettu työllistyminen": ["Työllisyyden hoitaminen", "Työllisyyspalvelut"],
    **dict.fromkeys(
        [
            "Terveyden ja hyvinvoinnin neuvonta- ja ohjauspalvelut",
            "Röntgen, laboratorio ja muut tutkimuspalvelut",
            "Oma- ja itsehoito",
            "Lääkkeet ja apteekit",
            "Terveyden vertais- ja vapaaehtoistoiminta",
            "Potilaan oikeudet",
            "Ravinto",
            "Eläinlääkäripalvelut",
        ],
        ["Terveyspalvelut"],
    ),
    **dict.fromkeys(["Neuvolapalvelut", "Kasvatus- ja perheneuvonta"], ["Neuvolat"]),
    "Päihde- ja mielenterveyspalvelut": ["Mielenterveys- ja päihdepalvelut"],
    "Suun ja hampaiden terveydenhuolto": ["Suun terveydenhuolto"],
    **dict.fromkeys(
        [
            "Terveydenhuolto, sairaanhoito ja ravitsemus",
            "Perusterveydenhuolto",
            "Rokotukset",
        ],
        ["Terveysaseman palvelut"],
    ),
    "Terveystarkastukset": ["Terveysaseman palvelut", "Työterveyshuolto"],
    **dict.fromkeys(
        [
            "Vanhusten palvelut",
            "Vammaisten muut kuin asumis- ja kotipalvelut",
            "Kotisairaanhoito ja omaishoito",
        ],
        ["Vanhus- ja vammaispalvelut"],
    ),
    "Työkyky ja ammatillinen kuntoutus": ["Työterveyshuolto", "Työllisyyspalvelut"],
    "Kuntoutus": ["Kuntoutumispalvelut"],
    **dict.fromkeys(
        ["Erikoissairaanhoito", "Ensiapu ja päivystys"],
        ["Erikoissairaanhoidon palvelut"],
    ),
    **dict.fromkeys(
        [
            "Työnhaku ja työpaikat",
            "Työelämän säännöt ja työehtosopimukset",
            "Yritysverotus",
            "Elintarviketuotanto",
        ],
        ["Työ- ja yrityspalvelut"],
    ),
    **dict.fromkeys(
        ["Työsuojelu", "Konkurssi"],
        ["Työ- ja yrityspalvelut", "Vaikuttaminen ja hallinto"],
    ),
    **dict.fromkeys(
        ["Palveluja työnantajalle", "Työnantajan palvelut"], ["Työllisyyspalvelut"]
    ),
    **dict.fromkeys(
        ["Henkilöstöhankinta", "Yrittäjäkoulutus"],
        ["Työllisyyspalvelut", "Palvelut yrityksille"],
    ),
    "Toimitilat": ["Tontit ja toimitilat"],
    **dict.fromkeys(
        [
            "Elinkeinot",
            "Yrityksen perustaminen",
            "Yritysyhteistyö ja verkostoituminen",
            "Yritystoiminnan lopettaminen",
            "Yrityskoulutus",
            "Liiketoiminnan kehittäminen",
            "Tuote- ja palvelukehitys",
            "Kansainvälistymispalvelut",
            "Omistajanvaihdos",
            "Tuonti ja vienti",
            "Yrityksen talous- ja velkaneuvonta",
            "Yritysrahoitus",
        ],
        ["Palvelut yrityksille"],
    ),
    "Rahoitusmarkkinat": ["Palvelut yrityksille", "Vaikuttaminen ja hallinto"],
    "Vakuutukset": [
        "Palvelut yrityksille",
        "Liikunta ja ulkoilu",
        "Vaikuttaminen ja hallinto",
    ],
    "Vapaa-ajan palvelut": ["Vapaa-aika", "Harrasteet"],
    "Uskonnot ja elämänkatsomukset": ["Vapaa-aika"],
    "Kirjastot": ["Kulttuuri", "Aineisto- ja tietopalvelut"],
    "Taiteet": ["Kulttuuri", "Museot", "Musiikkikohteet", "Näyttelyt", "Teatterit"],
    "Arkistot": ["Aineisto- ja tietopalvelut", "Vaikuttaminen ja hallinto"],
    "Tilasto- ja tietopalvelut": ["Aineisto- ja tietopalvelut"],
    **dict.fromkeys(
        [
            "Asiakirja- ja tietopyynnöt",
            "Rekisterit ja tietokannat",
            "Yleiset tieto- ja hallintopalvelut",
        ],
        [
            "Aineisto- ja tietopalvelut",
            "Vaikuttaminen ja hallinto",
        ],
    ),
    "Matkailu Suomessa": ["Nähtävyydet ja matkailuinfo"],
    "Liikunta ja urheilu": ["Liikunta ja ulkoilu"],
    "Retkeily": ["Ulkoilureitit", "Leirialueet ja saaret"],
    "Kalastus": ["Leirialueet ja saaret"],
    **dict.fromkeys(
        [
            "Demokratia",
            "Kansalaisvaikuttaminen",
            "Viranomaisten kuulutukset ja ilmoitukset",
            "Muuttaminen Suomen sisällä ja väestötiedot",
            "Kansalaisten perusoikeudet",
            "Vähemmistöt",
            "Puolueet",
            "Vaalit",
            "Kansalaisjärjestöjen toiminta",
            "Hallinnon yleiset neuvontapalvelut",
            "Viestintä",
            "Joukkoviestintä",
            "Tietoliikenne",
            "Postipalvelut",
            "Verotus ja julkinen talous",
            "Henkilöverotus",
            "Julkinen talous ja julkiset hankinnat",
            "Pankit",
            "Turvallisuus",
            "Löytötavarat",
            "Kuluttaja-asiat",
            "Kuluttajansuoja",
            "Maahan- ja maastamuutto",
            "Maahantuloluvat ja asiakirjat",
            "Kansalaisuuden hakeminen",
            "Muuttaminen Suomesta toiseen pohjoismaahan",
            "Muuttaminen Suomesta toiseen EU-valtioon",
            "Muuttaminen Suomesta EU:n ulkopuolelle",
            "Ulkosuomalaiset",
        ],
        ["Vaikuttaminen ja hallinto"],
    ),
}
