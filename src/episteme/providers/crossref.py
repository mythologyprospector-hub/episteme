"""Crossref REST API acquisition provider."""

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from ..acquisition import AcquisitionRequest, AcquisitionResponse
from ..capture import CaptureOutcome

CROSSREF_SOURCE_ID = "crossref"
CROSSREF_ACQUISITION_METHOD = "crossref-rest"
CROSSREF_ACQUISITION_METHOD_VERSION = "1"
CROSSREF_API_BASE = "https://api.crossref.org/v1/works"
USER_AGENT = "Episteme/0.1.0"


def fetch_works(
    request: AcquisitionRequest,
    timeout: float = 30.0,
) -> AcquisitionResponse:
    """Fetch one bounded Crossref /v1/works response."""
    if request.source_id != CROSSREF_SOURCE_ID:
        raise ValueError("Crossref provider requires source_id='crossref'")
    if request.acquisition_method != CROSSREF_ACQUISITION_METHOD:
        raise ValueError(
            "Crossref provider requires acquisition_method='crossref-rest'"
        )
    if request.acquisition_method_version != CROSSREF_ACQUISITION_METHOD_VERSION:
        raise ValueError(
            "Crossref provider requires acquisition_method_version='1'"
        )

    parsed = urlsplit(request.requested_resource)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.crossref.org"
        or parsed.path != "/v1/works"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Crossref requests must target the versioned https://api.crossref.org/v1/works endpoint"
        )

    parameters = dict(request.request_parameters)
    if "rows" in parameters:
        rows = parameters["rows"]
        if isinstance(rows, bool) or not isinstance(rows, int) or not 0 <= rows <= 1000:
            raise ValueError("Crossref rows must be an integer from 0 through 1000")

    query = urlencode(parameters, doseq=True)
    url = CROSSREF_API_BASE + (("?" + query) if query else "")
    http_request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )

    try:
        with urlopen(http_request, timeout=timeout) as response:
            content = response.read()
            media_type = response.headers.get_content_type()
            source_version = response.headers.get("ETag")
            return AcquisitionResponse(
                status=response.status,
                media_type=media_type,
                source_version=source_version,
                content=content,
                outcome=CaptureOutcome.COMPLETE,
            )
    except HTTPError as exc:
        return AcquisitionResponse(
            status=exc.code,
            media_type=exc.headers.get_content_type() if exc.headers else None,
            source_version=exc.headers.get("ETag") if exc.headers else None,
            content=None,
            outcome=CaptureOutcome.FAILED,
            error=f"HTTP {exc.code}: {exc.reason}",
        )
    except (URLError, TimeoutError) as exc:
        return AcquisitionResponse(
            status=None,
            media_type=None,
            source_version=None,
            content=None,
            outcome=CaptureOutcome.FAILED,
            error=f"{type(exc).__name__}: {exc}",
        )
