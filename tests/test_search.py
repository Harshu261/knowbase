
def test_search_finds_matching_document(client, db):
    from app.models import Document

    document = Document(
        title="Database Fundamentals",
        subject="DBMS",
        content=(
            "Database management systems organize "
            "and manage stored information."
        ),
    )
    db.add(document)
    db.commit()

    response = client.get(
        "/documents/search",
        params={"q": "database management"},
    )

    assert response.status_code == 200

    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Database Fundamentals"


def test_search_returns_empty_list_when_no_match(client):
    response = client.get(
        "/documents/search",
        params={"q": "quantum banana xyz"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_search_requires_query_parameter(client):
    response = client.get("/documents/search")

    assert response.status_code == 422

def test_search_rejects_whitespace_only_query(client):
    response = client.get(
        "/documents/search",
        params={"q": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Search query cannot be empty or whitespace."
    )


def test_search_orders_results_by_relevance(client, db):
    from app.models import Document

    less_relevant = Document(
        title="Basic Database Notes",
        subject="DBMS",
        content="Database management is important.",
    )

    more_relevant = Document(
        title="Detailed Database Notes",
        subject="DBMS",
        content=(
            "Database management improves database management. "
            "Database management is important."
        ),
    )

    db.add_all([less_relevant, more_relevant])
    db.commit()

    response = client.get(
        "/documents/search",
        params={"q": "database management"},
    )

    assert response.status_code == 200

    results = response.json()
    assert len(results) == 2
    assert results[0]["title"] == "Detailed Database Notes"
    assert results[1]["title"] == "Basic Database Notes"
