import uuid
from datetime import datetime

from django import db
from django.db.models import Max
from munigeo.importer.sync import ModelSyncher

from ptv.models import ServicePTVIdentifier
from ptv.utils import get_ptv_resource, UTC_TIMEZONE
from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
    update_service_root_service_nodes,
)
from services.models import Service, ServiceNode, Unit

TKU_PTV_NODE_MAPPING = {
    "Aamu- ja iltapäiväkerhotoiminta": "Perusopetus",
    "Aikuis- ja täydennyskoulutus": "Aikuiskoulutus",
    "Ammatinvalinta ja opintojen ohjaus": "Perusopetus",
    "Ammatinvalinta ja urasuunnittelu": "Aikuiskoulutus",
    "Arkistot": "Aineisto- ja tietopalvelut",
    "Asiakirja- ja tietopyynnöt": "Aineisto- ja tietopalvelut",
    "Asumispalvelut": "Tuet ja etuudet",
    "Elinkeinot": "Työ- ja yrityspalvelut",
    "Erikoissairaanhoito": "Erikoissairaanhoidon palvelut",
    "Esiopetus": "Päivähoito ja esiopetus",
    "Henkilöstöhankinta": "Työllisyyspalvelut",
    "Henkilöstön kehittäminen": "Työ- ja yrityspalvelut",
    "Hyvinvointipalvelujen tukipalvelut": "Sosiaalipalvelut",
    "Jätehuolto": "Asuminen",
    "Kansainvälistymispalvelut": "Palvelut yrityksille",
    "Kiinteistöt": "Kaavoitus, kiinteistöt ja rakentaminen",
    "Kirjastot ja tietopalvelut": "Aineisto- ja tietopalvelut",
    "Korkeakoulutus": "Ammattikorkeakoulut ja yliopistot",
    "Korjaus- ja energia-avustukset": "Kaavoitus, kiinteistöt ja rakentaminen",
    "Kotihoito ja kotipalvelut": "Tuet ja etuudet",
    "Kotisairaanhoito ja omaishoito": "Vanhus- ja vammaispalvelut",
    "Koulu- ja opiskelijahuollon sosiaalipalvelut": "Muu sosiaalihuolto",
    "Koulu- ja opiskelijaterveydenhuolto": "Koulu- ja opiskeluterveydenhuolto",
    "Koulutus": "Päivähoito ja koulutus",
    "Kuntoutus": "Kuntoutumispalvelut",
    "Lasten päivähoito": "Päivähoito ja esiopetus",
    "Liiketoiminnan kehittäminen": "Palvelut yrityksille",
    "Liikunta ja urheilu": "Liikunta ja ulkoilu",
    "Maankäyttö, kaavoitus ja tontit": "Kaavoitus, kiinteistöt ja rakentaminen",
    "Neuvolapalvelut": "Neuvolat",
    "Oikeusturva": "Oikeudelliset palvelut",
    "Omistajanvaihdos": "Palvelut yrityksille",
    "Oppisopimus": "Ammatillinen koulutus",
    "Päihde- ja mielenterveyspalvelut": "Mielenterveys- ja päihdepalvelut",
    "Perheiden palvelut": "Lapsiperheen tuet",
    "Perusterveydenhuolto": "Terveyspalvelut",
    "Rakentaminen": "Kaavoitus, kiinteistöt ja rakentaminen",
    "Retkeily": "Leirialueet ja saaret",
    "Rokotukset": "Koulu- ja opiskeluterveydenhuolto",
    "Röntgen, laboratorio ja muut tutkimuspalvelut": "Terveyspalvelut",
    "Sosiaalipalvelujen neuvonta- ja ohjauspalvelut": "Sosiaalipalvelut",
    "Sosiaalipalvelujen oheis- ja tukipalvelut": "Tuet ja etuudet",
    "Suun ja hampaiden terveydenhuolto": "Suun terveydenhuolto",
    "Taiteet": "Kulttuuri",
    "Terveyden ja hyvinvoinnin neuvonta- ja ohjauspalvelut": "Terveysaseman palvelut",
    "Terveydenhuolto, sairaanhoito ja ravitsemus": "Terveysaseman palvelut",
    "Terveystarkastukset": "Työterveyshuolto",
    "Tienpito": "Liikenne",
    "Tilaisuuksien järjestäminen": "Tontit ja toimitilat",
    "Toimialakohtaiset luvat ja velvoitteet": "Asuminen ja ympäristö",
    "Toimitilat": "Tontit ja toimitilat",
    "Toisen asteen ammatillinen koulutus": "Ammatillinen koulutus",
    "Työ ja työttömyys": "Työllisyyspalvelut",
    "Työelämän säännöt ja työehtosopimukset": "Työ- ja yrityspalvelut",
    "Työkyky ja ammatillinen kuntoutus": "Työllisyyspalvelut",
    "Työnantajan palvelut": "Palvelut yrityksille",
    "Työnhaku ja työpaikat": "Työ- ja yrityspalvelut",
    "Väestönsuojelu": "Turvallisuus",
    "Vammaisten muut kuin asumis- ja kotipalvelut": "Vanhus- ja vammaispalvelut",
    "Vanhusten palvelut": "Vanhus- ja vammaispalvelut",
    "Vapaa sivistystyö ja taidekasvatus": "Päivähoito ja koulutus",
    "Vapaa-ajan palvelut": "Vapaa-aika",
    "Vesihuolto": "Asuminen ja ympäristö",
    "Vuokra-asuminen": "Asuminen",
    "Yleiset tieto- ja hallintopalvelut": "Aineisto- ja tietopalvelut",
    "Ympäristöilmoitukset ja luvat": "Asuminen ja ympäristö",
    "Yrityksen perustaminen": "Palvelut yrityksille",
    "Yrityksen talous- ja velkaneuvonta": "Palvelut yrityksille",
    "Yrityskoulutus": "Palvelut yrityksille",
    "Yritysrahoitus": "Palvelut yrityksille",
    "Yritystoiminnan lopettaminen": "Palvelut yrityksille",
}


class PTVServiceImporter:
    service_syncher = ModelSyncher(
        Service.objects.filter(ptv_id__isnull=False), lambda obj: obj.id
    )
    service_id_syncher = ModelSyncher(
        ServicePTVIdentifier.objects.all(), lambda obj: obj.id
    )

    def __init__(self, area_code, logger=None):
        self.are_code = area_code
        self.logger = logger

    @db.transaction.atomic
    def import_services(self):
        data = get_ptv_resource(self.are_code, "service")
        page_count = data["pageCount"]
        for page in range(1, page_count + 1):
            if page > 1:
                data = get_ptv_resource(
                    self.are_code, resource_name="service", page=page
                )
            self._import_services(data)

        self._clean_services()
        update_service_counts()

    def _import_services(self, data):
        id_counter = 1
        for service in data["itemList"]:
            self._handle_service(service, id_counter)
            id_counter += 1

    def _handle_service(self, service_data, id_counter):
        uuid_id = uuid.UUID(service_data.get("id"))
        id_obj = self.service_id_syncher.get(uuid_id)
        # Only import services related to the imported units, therefore their ids should be found.
        if not id_obj:
            return

        if id_obj.service:
            service_id = id_obj.service.id
        else:
            # Create an id by getting next available id since AutoField is not in use.
            service_id = (
                Service.objects.aggregate(Max("id"))["id__max"] or 0
            ) + id_counter

        service_obj = self.service_syncher.get(service_id)
        if not service_obj:
            service_obj = Service(
                id=service_id, clarification_enabled=False, period_enabled=False
            )
            service_obj._changed = True

        if not id_obj.service:
            id_obj.service = service_obj
            id_obj._changed = True
            self._save_object(id_obj)

        self._handle_service_names(service_data, service_obj)
        self._save_object(service_obj)
        self._handle_units(service_data, service_obj)
        self._handle_service_nodes(service_data, service_obj)

    def _handle_service_names(self, service_data, service_obj):
        for name in service_data.get("serviceNames"):
            lang = name.get("language")
            value = name.get("value")
            obj_key = "{}_{}".format("name", lang)
            setattr(service_obj, obj_key, value)

    def _handle_units(self, service_data, service_obj):
        for channel in service_data.get("serviceChannels"):
            unit_uuid = uuid.UUID(channel.get("serviceChannel").get("id"))
            try:
                unit_obj = Unit.objects.get(ptv_id__id=unit_uuid)
                service_obj.units.add(unit_obj)
                unit_obj.root_service_nodes = ",".join(
                    str(x) for x in unit_obj.get_root_service_nodes()
                )
                unit_obj._changed = True
                self._save_object(unit_obj)

            except Unit.DoesNotExist:
                continue

    def _handle_service_nodes(self, service_data, service_obj):
        for service_class in service_data.get("serviceClasses"):
            self._handle_service_node(service_class, service_obj)
        update_service_node_counts()
        update_service_root_service_nodes()

    def _handle_service_node(self, node, service_obj):
        for name in node.get("name"):
            if name.get("language") == "fi":
                value = name.get("value")
                # TODO: Alternative solution to the Turku mapping
                if value in TKU_PTV_NODE_MAPPING:
                    value = TKU_PTV_NODE_MAPPING.get(value)

                node_obj = ServiceNode.objects.filter(name=value).first()
                if not node_obj:
                    # TODO: What to do with the nodes that can't be mapped to the existing ones.
                    self.logger.warning(
                        'ServiceNode "{}" does not exist!'.format(value)
                    )
                    break

                node_obj.related_services.add(service_obj)
                node_obj.units.add(*service_obj.units.all())
                node_obj._changed = True
                self._save_object(node_obj)

    def _clean_services(self):
        Service.objects.filter(units__isnull=True, ptv_id__isnull=False).delete()

    def _save_object(self, obj):
        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
