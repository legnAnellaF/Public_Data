from backend.app.schemas.intent import SearchRequest


def test_search_request_accepts_existing_payload_without_target_link() -> None:
    request = SearchRequest(query="서울 미세먼지")

    assert request.query == "서울 미세먼지"
    assert request.target_link is None


def test_search_request_accepts_optional_target_link() -> None:
    request = SearchRequest(
        query="서울 미세먼지",
        target_link="https://www.data.go.kr/tcs/dss/selectFileDataDetailView.do?publicDataPk=test",
    )

    assert request.target_link == "https://www.data.go.kr/tcs/dss/selectFileDataDetailView.do?publicDataPk=test"
