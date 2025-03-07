import pytest
from rest_framework.reverse import reverse

from services.search.api import build_search_query


@pytest.mark.django_db
def test_search(
    api_client,
    units,
    streets,
    services,
    service_nodes,
    addresses,
    administrative_division,
    accessibility_shortcoming,
    municipality,
    exclusion_rules,
    exclusion_words,
):
    # Search for "museo" in entities: units,services and servicenods
    url = reverse("search") + "?q=museo&type=unit,service,servicenode"
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    # Should find one Unit, one Service and one ServiceNode
    assert len(results) == 3
    # Test that all Unit fields are serialized
    biological_museum_unit = results[0]
    assert biological_museum_unit["object_type"] == "unit"
    assert biological_museum_unit["name"]["fi"] == "Biologinen museo"
    assert biological_museum_unit["name"]["sv"] == "Biologiska museet"
    assert biological_museum_unit["name"]["en"] == "Biological Museum"
    assert biological_museum_unit["street_address"]["fi"] == "Neitsytpolku 1"
    assert biological_museum_unit["municipality"] == "helsinki"
    assert biological_museum_unit["contract_type"]["id"] == "municipal_service"

    assert (
        biological_museum_unit["contract_type"]["description"]["fi"]
        == "kunnallinen palvelu"
    )
    assert (
        biological_museum_unit["contract_type"]["description"]["sv"]
        == "kommunal tjänst"
    )
    assert (
        biological_museum_unit["contract_type"]["description"]["en"]
        == "municipal service"
    )
    assert biological_museum_unit["department"]["name"]["fi"] == "Test Department"
    assert (
        biological_museum_unit["department"]["street_address"]["fi"]
        == "Test Address 42"
    )
    assert biological_museum_unit["department"]["municipality"] == "helsinki"
    assert biological_museum_unit["accessibility_shortcoming_count"]["rollator"] == 5
    assert biological_museum_unit["accessibility_shortcoming_count"]["stroller"] == 1
    assert biological_museum_unit["location"]["type"] == "Point"
    assert biological_museum_unit["location"]["coordinates"][0] == 22.24
    assert biological_museum_unit["location"]["coordinates"][1] == 60.44
    # Test Service fields.
    museum_service = results[1]
    assert museum_service
    assert museum_service["object_type"] == "service"
    assert museum_service["name"]["fi"] == "Museot"
    assert museum_service["name"]["sv"] == "Museum"
    assert museum_service["name"]["en"] == "Museum"
    assert museum_service["unit_count"]["municipality"]["helsinki"] == 1
    assert museum_service["unit_count"]["total"] == 1
    assert museum_service["root_service_node"]["name"]["fi"] == "Vapaa-aika"
    assert museum_service["root_service_node"]["name"]["sv"] == "Fritid"
    assert museum_service["root_service_node"]["name"]["en"] == "Leisure"
    # Test ServiceNode fields
    museum_service_node = results[2]
    assert museum_service_node["object_type"] == "servicenode"
    assert museum_service_node["ids"] == ["2"]
    assert museum_service_node["name"]["fi"] == "Museot"
    assert museum_service_node["name"]["sv"] == "Museer"
    assert museum_service_node["name"]["en"] == "Museums"
    assert museum_service_node["root_service_node"]["name"]["fi"] == "Vapaa-aika"
    assert museum_service_node["root_service_node"]["name"]["sv"] == "Fritid"
    assert museum_service_node["root_service_node"]["name"]["en"] == "Leisure"
    assert museum_service_node["unit_count"]["municipality"]["helsinki"] == 1
    assert museum_service_node["unit_count"]["total"] == 1
    # Test that unit "Impivaara" is retrieved from service Uimahalli
    url = reverse("search") + "?q=uimahalli&type=unit&rank_threshold=0"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["name"]["fi"] == "Impivaara"
    assert results[0]["object_type"] == "unit"
    # Test syllables and include parameter by searching "asema"
    url = reverse("search") + "?q=asema&type=unit&include=unit.www,unit.phone"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["object_type"] == "unit"
    assert results[0]["name"]["fi"] == "Terveysasema"
    assert results[0]["www"] == "www.test.com"
    assert results[0]["phone"] == "02020242"
    # Test municipality parameter.
    url = reverse("search") + "?q=museo&type=unit&municipality=raisio"
    response = api_client.get(url)
    results = response.json()["results"]
    # No results for municipality "Raisio".
    assert len(results) == 0
    # Test address search and serialization.
    url = reverse("search") + "?q=kurra&type=address"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 1
    kurrapolku = results[0]
    assert kurrapolku["object_type"] == "address"
    assert kurrapolku["name"]["fi"] == "Kurrapolku 1A"
    assert kurrapolku["name"]["sv"] == "Kurrastigen 1A"
    assert kurrapolku["name"]["en"] == "Kurrapolku 1A"
    assert kurrapolku["number"] == "1"
    assert kurrapolku["number_end"] == "2"
    assert kurrapolku["letter"] == "A"
    assert kurrapolku["municipality"]["id"] == "helsinki"
    assert kurrapolku["municipality"]["name"]["fi"] == "Helsinki"
    assert kurrapolku["municipality"]["name"]["sv"] == "Helsingfors"
    assert kurrapolku["street"]["name"]["fi"] == "Kurrapolku"
    assert kurrapolku["street"]["name"]["sv"] == "Kurrastigen"
    assert kurrapolku["location"]["type"] == "Point"
    assert kurrapolku["location"]["coordinates"][0] == 60.479032
    assert kurrapolku["location"]["coordinates"][1] == 22.25417
    # Test search with excluded word
    url = reverse("search") + "?q=katu"
    response = api_client.get(url)
    assert response.status_code == 400
    url = reverse("search") + "?q=Katu"
    response = api_client.get(url)
    assert response.status_code == 400
    url = reverse("search") + "?q=koti katu"
    response = api_client.get(url)
    assert response.status_code == 400
    # Test search with 'kello'
    url = reverse("search") + "?q=kello&type=address"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["name"]["fi"] == "Kellonsoittajankatu 1"
    # Test address search with apostrophe in query
    url = reverse("search") + "?q=tarkk'ampujankatu&type=address"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["name"]["fi"] == "Tarkk'ampujankatu 1"
    # Test that addresses are sorted by naturalsort.
    url = reverse("search") + "?q=yliopistonkatu&type=address"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["name"]["fi"] == "Yliopistonkatu 5"
    assert results[1]["name"]["fi"] == "Yliopistonkatu 21"
    assert results[2]["name"]["fi"] == "Yliopistonkatu 33"
    # Test administrative division search.
    url = reverse("search") + "?q=hel&type=administrativedivision"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["object_type"] == "administrativedivision"
    assert results[0]["name"]["fi"] == "Helsinki"


@pytest.mark.django_db
def test_search_service_order(api_client, units, services):
    """
    Test that services are ordered descending by unit count.
    """
    url = reverse("search") + "?q=halli&type=service"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 3

    assert results[0]["name"]["fi"] == "Halli"
    assert results[0]["unit_count"]["total"] == 2

    assert results[1]["name"]["fi"] == "Uimahalli"
    assert results[1]["unit_count"]["total"] == 1

    assert results[2]["name"]["fi"] == "Hallinto"
    assert results[2]["unit_count"]["total"] == 0


@pytest.mark.parametrize(
    "query",
    [
        "halli|museo",  # Test |
        "halli&museo",  # Test &
        "linja-auto",  # Test -
        "Keskustakirjasto Oodi",  # Test whitespace
        "Keskustakirjasto+Oodi",  # Test +
        # Test ääkköset
        "lääkäri",
        "röntgen",
        "åbo",
        "123",  # Test number
        "halli.museo",  # Test .
        "halli's",  # Test '
        "halli,museo",  # Test ,
    ],
)
@pytest.mark.django_db
def test_search_input_query_valid_characters(api_client, query):
    url = reverse("search")
    response = api_client.get(url, {"q": query})
    assert response.status_code == 200


@pytest.mark.django_db
def test_search_input_query_disallowed_characters(api_client):
    url = reverse("search")
    response = api_client.get(url, {"q": "halli("})
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid search terms, only letters, numbers, spaces and .,'+-&| allowed."
    )


@pytest.mark.django_db
def test_search_with_vertical_bar_in_query(api_client, units):
    # Test that a vertical bars that are not between search terms do not cause an error
    url = reverse("search") + "?q=|terveysasema||''||'"
    response = api_client.get(url)
    assert response.status_code == 200, f"{response} {response.json()}"


@pytest.mark.parametrize(
    "query,expected",
    [
        # Single-operand expression
        ("a", "a:*"),
        ("|a|", "a:*"),
        ("&a&", "a:*"),
        (" a ", "a:*"),
        ("& |a  || &|&    &&", "a:*"),
        # Two-operand expressions with AND operator
        ("a b", "a:* & b:*"),
        ("a,b", "a:* & b:*"),
        ("a, b", "a:* & b:*"),
        ("a,,, , ,, , , , ,   ,  ,,  ,        b", "a:* & b:*"),
        ("a & b", "a:* & b:*"),
        ("a& b", "a:* & b:*"),
        ("a &b", "a:* & b:*"),
        ("a&b", "a:* & b:*"),
        ("a&&&&&&&&&&&&&b", "a:* & b:*"),
        ("a  , &&&&&&&,    &  ,, & & & & &&&&& , , ,,,,      b", "a:* & b:*"),
        # Two-operand expressions with OR operator
        ("a | b", "a:* | b:*"),
        ("a | b", "a:* | b:*"),
        ("a| b", "a:* | b:*"),
        ("a |b", "a:* | b:*"),
        ("a|b", "a:* | b:*"),
        ("a|||||||||||||b", "a:* | b:*"),
        ("a ||| |||    ||  | ||| b", "a:* | b:*"),
        # >=3 operands
        ("a | b | c", "a:* | b:* | c:*"),
        ("a, b, c", "a:* & b:* & c:*"),
        ("a & b c, d", "a:* & b:* & c:* & d:*"),
        # Mixed OR and AND operators
        ("a, b | c, d", "a:* & b:* | c:* & d:*"),
        ("a, &&& , & b || || |||| |c,,,, d", "a:* & b:* | c:* & d:*"),
        # Expression with repeating single-quotes
        ("','','''',a,b'c,d''e,f'''g,','','''", "a:* & b'c:* & d''e:* & f'''g:*"),
    ],
)
def test_build_search_query(query, expected):
    assert build_search_query(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        "palloilu, halli",
        "palloilu,halli",
        "palloilu,     halli",
        "palloilu,,,,,,halli",
        "palloilu halli",
        "palloilu    halli",
        ",palloilu,halli",
        "palloilu,halli,,",
    ],
)
@pytest.mark.django_db
def test_search_input_and_operator(api_client, units, query):
    url = reverse("search")
    response = api_client.get(url, {"q": query, "type": "unit"})
    assert response.status_code == 200, f"{response} {response.json()}"
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"]["fi"] == "Palloiluhalli"


@pytest.mark.parametrize(
    "query",
    [
        "terveysasema|museo",
        "terveysasema | museo",
        "terveysasema |museo",
        "terveysasema| museo",
        "      terveysasema     |      museo  ",
        "terveysasema||museo",
        "terveysasema|||||||||museo",
        "|||terveysasema|museo||",
    ],
)
@pytest.mark.django_db
def test_search_input_or_operator(api_client, units, query):
    url = reverse("search")
    response = api_client.get(url, {"q": query, "type": "unit"})
    assert response.status_code == 200, f"{response} {response.json()}"
    assert len(response.json()["results"]) == 2
    assert response.json()["results"][0]["name"]["fi"] == "Terveysasema"
    assert response.json()["results"][1]["name"]["fi"] == "Biologinen museo"


@pytest.mark.django_db
def test_search_with_bbox_parameter(api_client, units):
    """
    When bbox parameter is given, only units within the bounding box should be returned.
    """
    url = reverse("search") + "?q=halli&type=unit"
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 3

    url = (
        reverse("search")
        + "?q=halli&type=unit&bbox=24.93545,60.16952,24.95190,60.17800&bbox_srid=4326"
    )
    response = api_client.get(url)
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["name"]["fi"] == "Jäähalli"
