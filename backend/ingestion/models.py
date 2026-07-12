from pydantic import BaseModel


class DocChunk(BaseModel):
    """A page-and-bbox-anchored slice of parsed document text or table content.

    Every chunk must carry provenance back to a specific location in the
    source PDF — without it we cannot draw the highlight box on the PDF, and
    the highlight box is the demo (see CLAUDE.md).
    """

    text: str
    source_doc: str
    page: int
    bbox: tuple[float, float, float, float]
    is_table: bool = False
