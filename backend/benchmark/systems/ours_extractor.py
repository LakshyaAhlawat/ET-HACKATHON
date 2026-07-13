"""Re-exports the production FACT-tag extractor
(app/services/compliance/corpus_extractor.py) so the benchmark harness and
the query router (Session 7) share one implementation -- kept so existing
`from benchmark.systems.ours_extractor import ...` call sites don't need to
change."""

from app.services.compliance.corpus_extractor import (
    extract_corpus_facts as extract_corpus_facts,
)
from app.services.compliance.corpus_extractor import (
    find_extracted_values as find_extracted_values,
)
from app.services.compliance.corpus_extractor import find_requirement as find_requirement
from app.services.compliance.corpus_extractor import (
    find_requirement_by_equipment as find_requirement_by_equipment,
)
