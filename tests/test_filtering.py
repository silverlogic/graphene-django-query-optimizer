import pytest

from tests.factories import (
    ApartmentFactory,
    BuildingFactory,
    HousingCompanyFactory,
    PropertyManagerFactory,
    RealEstateFactory,
)
from tests.helpers import has

pytestmark = [
    pytest.mark.django_db,
]


def test_filter__to_one_relation(graphql_client):
    HousingCompanyFactory.create(name="1", postal_code__code="00001")
    HousingCompanyFactory.create(name="2", postal_code__code="00002")
    HousingCompanyFactory.create(name="3", postal_code__code="00003")

    query = """
        query {
          pagedHousingCompanies(postalCode_Code_Iexact: "00001") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting housing companies.
    # 1 query for fetching housing companies.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_housingcompany"',
    )
    assert response.queries[1] == has(
        'FROM "example_housingcompany"',
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "1"}},
        ],
    }


def test_filter__to_many_relation(graphql_client):
    HousingCompanyFactory.create(name="1", developers__name="1")
    HousingCompanyFactory.create(name="2", developers__name="2")
    HousingCompanyFactory.create(name="3", developers__name="3")

    query = """
        query {
          pagedHousingCompanies(developers_Name_Iexact: "1") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting housing companies.
    # 1 query for fetching housing companies.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_housingcompany"',
    )
    assert response.queries[1] == has(
        'FROM "example_housingcompany"',
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "1"}},
        ],
    }


def test_filter__custom_filter(graphql_client):
    HousingCompanyFactory.create(name="1", street_address="Example", postal_code__code="00001", city="Helsinki")
    HousingCompanyFactory.create(name="2", street_address="Other", postal_code__code="00002", city="London")
    HousingCompanyFactory.create(name="3", street_address="Thing", postal_code__code="00003", city="Paris")

    query = """
        query {
          pagedHousingCompanies(address: "00001") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting housing companies.
    # 1 query for fetching housing companies.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_housingcompany"',
    )
    assert response.queries[1] == has(
        'FROM "example_housingcompany"',
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "1"}},
        ],
    }


def test_filter__order_by(graphql_client):
    HousingCompanyFactory.create(name="1")
    HousingCompanyFactory.create(name="3")
    HousingCompanyFactory.create(name="2")

    query = """
        query {
          pagedHousingCompanies(orderBy: "name") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting housing companies.
    # 1 query for fetching housing companies.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_housingcompany"',
    )
    assert response.queries[1] == has(
        'FROM "example_housingcompany"',
    )

    assert response.content == {
        "edges": [
            {"node": {"name": "1"}},
            {"node": {"name": "2"}},
            {"node": {"name": "3"}},
        ],
    }


def test_filter__list_field(graphql_client):
    ApartmentFactory.create(street_address="1")
    ApartmentFactory.create(street_address="2")
    ApartmentFactory.create(street_address="3")

    query = """
        query {
          allApartments(streetAddress:"1") {
            streetAddress
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for fetching apartments.
    assert response.queries.count == 1, response.queries.log

    assert response.queries[0] == has(
        'FROM "example_apartment"',
    )

    assert response.content == [{"streetAddress": "1"}]


def test_filter__nested_list_field(graphql_client):
    BuildingFactory.create(name="1", apartments__street_address="1")
    BuildingFactory.create(name="2", apartments__street_address="2")
    BuildingFactory.create(name="3", apartments__street_address="3")

    query = """
        query {
          allBuildings {
            apartments(streetAddress:"1") {
              streetAddress
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for fetching buildings.
    # 1 query for fetching apartments.
    assert response.queries.count == 2, response.queries.log

    assert response.queries[0] == has(
        'FROM "example_building"',
    )
    assert response.queries[1] == has(
        'FROM "example_apartment"',
    )

    assert response.content == [
        {
            "apartments": [{"streetAddress": "1"}],
        },
        {
            "apartments": [],
        },
        {
            "apartments": [],
        },
    ]


def test_filter__nested_connection(graphql_client):
    PropertyManagerFactory.create(housing_companies__name="1")
    PropertyManagerFactory.create(housing_companies__name="2")
    PropertyManagerFactory.create(housing_companies__name="3")

    query = """
        query {
          pagedPropertyManagers {
            edges {
              node {
                housingCompanies(name_Iexact: "1") {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting property managers.
    # 1 query for fetching property managers.
    # 1 query for fetching related housing companies.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_propertymanager"',
    )
    assert response.queries[1] == has(
        'FROM "example_propertymanager"',
        "LIMIT 3",
    )
    # Check that the filter is actually applied
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany"."property_manager_id" ORDER BY "example_housingcompany"."id")'
        ),
    )

    assert response.content == {
        "edges": [
            {"node": {"housingCompanies": {"edges": [{"node": {"name": "1"}}]}}},
            {"node": {"housingCompanies": {"edges": []}}},
            {"node": {"housingCompanies": {"edges": []}}},
        ]
    }


def test_filter__nested_connection__deep(graphql_client):
    PropertyManagerFactory.create(housing_companies__real_estates__name="1")
    PropertyManagerFactory.create(housing_companies__real_estates__name="2")
    PropertyManagerFactory.create(housing_companies__real_estates__name="3")

    query = """
        query {
          pagedPropertyManagers {
            edges {
              node {
                housingCompanies {
                  edges {
                    node {
                      realEstates(name:"1") {
                        edges {
                          node {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting property managers.
    # 1 query for fetching property managers.
    # 1 query for fetching housing companies.
    # 1 query for fetching real estates.
    assert response.queries.count == 4, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_propertymanager"',
    )
    assert response.queries[1] == has(
        'FROM "example_propertymanager"',
        "LIMIT 3",
    )
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany"."property_manager_id" ORDER BY "example_housingcompany"."id")'
        ),
    )
    assert response.queries[3] == has(
        'FROM "example_realestate"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_realestate"."housing_company_id" ORDER BY "example_realestate"."id")'
        ),
    )

    assert response.content == {
        "edges": [
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {
                                "node": {
                                    "realEstates": {
                                        "edges": [
                                            {"node": {"name": "1"}},
                                        ],
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {
                                "node": {
                                    "realEstates": {
                                        "edges": [],
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            {
                "node": {
                    "housingCompanies": {
                        "edges": [
                            {
                                "node": {
                                    "realEstates": {
                                        "edges": [],
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        ]
    }


def test_filter__nested_connection__fragment_spread(graphql_client):
    PropertyManagerFactory.create(housing_companies__name="1")
    PropertyManagerFactory.create(housing_companies__name="2")
    PropertyManagerFactory.create(housing_companies__name="3")

    query = """
        fragment Companies on PropertyManagerNode {
          housingCompanies(name_Iexact: "1") {
            edges {
              node {
                name
              }
            }
          }
        }
        query {
          pagedPropertyManagers {
            edges {
              node {
                ...Companies
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.no_errors, response.errors

    # 1 query for counting property managers.
    # 1 query for fetching property managers.
    # 1 query for fetching housing companies.
    assert response.queries.count == 3, response.queries.log

    assert response.queries[0] == has(
        "COUNT(*)",
        'FROM "example_propertymanager"',
    )
    assert response.queries[1] == has(
        'FROM "example_propertymanager"',
        "LIMIT 3",
    )
    assert response.queries[2] == has(
        'FROM "example_housingcompany"',
        (
            "ROW_NUMBER() OVER "
            '(PARTITION BY "example_housingcompany"."property_manager_id" ORDER BY "example_housingcompany"."id")'
        ),
    )

    assert response.content == {
        "edges": [
            {"node": {"housingCompanies": {"edges": [{"node": {"name": "1"}}]}}},
            {"node": {"housingCompanies": {"edges": []}}},
            {"node": {"housingCompanies": {"edges": []}}},
        ]
    }


def test_filter__invalid_value(graphql_client):
    RealEstateFactory.create(name="1", surface_area=1)
    RealEstateFactory.create(name="2", surface_area=2)
    RealEstateFactory.create(name="3", surface_area=3)

    query = """
        query {
          pagedRealEstates(surfaceArea: "foo") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.errors[0]["message"] == """Expected value of type 'Decimal', found "foo"."""


def test_filter__aliased_queries(graphql_client):
    building_1 = BuildingFactory.create(name="1")
    apartment_1 = ApartmentFactory.create(street_address="A01", building=building_1)
    apartment_2 = ApartmentFactory.create(street_address="B01", building=building_1)
    ApartmentFactory.create(street_address="C01", building=building_1)

    building_2 = BuildingFactory.create(name="2")
    apartment_3 = ApartmentFactory.create(street_address="A10", building=building_2)
    ApartmentFactory.create(street_address="C11", building=building_2)

    building_3 = BuildingFactory.create(name="3")
    apartment_4 = ApartmentFactory.create(street_address="B20", building=building_3)

    query = """
        query {
          buildings: pagedBuildings(orderBy: "name") {
            edges {
              node {
                pk
                name
                A: apartments(streetAddress_Istartswith: "A") {
                  edges {
                    node {
                      pk
                    }
                  }
                }
                B: apartments(streetAddress_Istartswith: "B") {
                  edges {
                    node {
                      pk
                    }
                  }
                }
              }
            }
          }
          all: pagedBuildings(orderBy: "-name") {
            edges {
              node {
                name
              }
            }
          }
        }
    """

    response = graphql_client(query)
    assert response.full_content == {
        "data": {
            "buildings": {
                "edges": [
                    {
                        "node": {
                            "pk": building_1.pk,
                            "name": building_1.name,
                            "A": {
                                "edges": [
                                    {"node": {"pk": apartment_1.pk}},
                                ],
                            },
                            "B": {
                                "edges": [
                                    {"node": {"pk": apartment_2.pk}},
                                ],
                            },
                        },
                    },
                    {
                        "node": {
                            "pk": building_2.pk,
                            "name": building_2.name,
                            "A": {
                                "edges": [
                                    {"node": {"pk": apartment_3.pk}},
                                ],
                            },
                            "B": {
                                "edges": [],
                            },
                        },
                    },
                    {
                        "node": {
                            "pk": building_3.pk,
                            "name": building_3.name,
                            "A": {
                                "edges": [],
                            },
                            "B": {
                                "edges": [
                                    {"node": {"pk": apartment_4.pk}},
                                ],
                            },
                        },
                    },
                ],
            },
            "all": {
                "edges": [
                    {"node": {"name": building_3.name}},
                    {"node": {"name": building_2.name}},
                    {"node": {"name": building_1.name}},
                ]
            },
        }
    }

    assert response.queries.count == 6, response.queries.log
