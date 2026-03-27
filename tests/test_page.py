from sentinel.models.license import License
from sentinel.models.page import Page


def test_page_from_json(sample_license_json):
    from tests.conftest import SAMPLE_PAGE_JSON

    page_data = SAMPLE_PAGE_JSON["page"]
    licenses = [License.model_validate(item) for item in page_data["content"]]
    meta = page_data["page"]
    page = Page(
        content=licenses,
        size=meta["size"],
        number=meta["number"],
        total_elements=meta["totalElements"],
        total_pages=meta["totalPages"],
    )
    assert page.size == 50
    assert page.number == 0
    assert page.total_elements == 1
    assert page.total_pages == 1
    assert len(page.content) == 1
    assert page.content[0].key == "KEY-ABC-123"
