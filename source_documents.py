from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from card_models import BaseMetadata

PAGE_DOT_PATTERN = r"^\s*(?P<marker>[\*_]*[pP]\\?\.\s*[\*_]*(?P<page>\d+(?:\s*[-–—]\s*\d+)?)(?:\s*\.)?)"
# Handles typical year+page citations like "PUTNAM, H. (1990:16-17)." and variants such as
# "PUTNAM, H. (1990:13-14 y 15)." by capturing the page text exactly as matched.
PARENTHESIS_YEAR_PAGE_PATTERN = r"^\s*(?P<marker>[A-ZÁÉÍÓÚÜÑ][^()]{1,180}?\((?P<year>\d{4}(?:-\d{4})?)\s*:\s*(?P<page>\(?[^)\n]+?\)?)\)(?:\.)?)"
# Levinson 2004 mixes markers like "LEVINSON, S. C. (2004:30)." with
# "LEVINSON, S. (2004 (2000): 31)." and also contains in-body citations that
# should not be treated as split markers.
LEVINSON_2004_PATTERN = r"^\s*(?P<marker>LEVINSON,\s*S\.(?:\s*C\.)?\s*\((?P<year>\d{4})(?:\s*\(\d{4}\))?\s*:\s*(?P<page>\d+(?:[’'])?(?:\s*[-–—]\s*\d+(?:[’'])?)?)\)?(?:\.)?)"
# Warnock mixes standalone page lines with running headers such as
# "Truth p.43" and "Conocimiento y otras mentes p. 25".
WARNOCK_PAGE_PATTERN = r"^\s*(?:[^\n]{0,80}?\s+)?(?P<marker>[Pp]\.?\s*(?P<page>\d+(?:\s*[-–—]\s*\d+)?))(?:\s+[^\n]{0,80})?\s*$"


@dataclass(kw_only=True)
class SourceDocumentConfig(BaseMetadata):
    filename: str
    split_pattern: str
    extra: dict[str, str] = field(default_factory=dict)


class SourceDocument(Enum):
    AVRANMIDES_2019 = SourceDocumentConfig(
        filename="Avranmides 2019 Knowing Other Minds.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="Knowing Other Minds",
        author="Avramides",
        book="Knowing Other Minds",
        year="2019",
    )
    CUENCA_HILFERTY_1999 = SourceDocumentConfig(
        filename="Cuenca y Hilferty 1999 Intruducción a la lingüística cognitiva.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="Introducción a la lingüística cognitiva",
        author="Cuenca y Hilferty",
        book="Introducción a la lingüística cognitiva",
        year="1999",
    )
    DAVIDSON_1990 = SourceDocumentConfig(
        filename="Davidson 1990 De la verdad y de la interpretación.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="De la verdad y de la interpretación",
        author="Davidson",
        book="De la verdad y de la interpretación",
        year="1990",
    )
    ECO_1992 = SourceDocumentConfig(
        filename="Eco 1992 Los límites de la interpretación.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Los límites de la interpretación",
        author="Eco",
        book="Los límites de la interpretación",
        year="1992",
    )
    FONTANILLE_2008 = SourceDocumentConfig(
        filename="Fontanille 2008 SOMA y SEMA.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="SOMA y SEMA",
        author="Fontanille",
        book="SOMA y SEMA",
        year="2008",
    )
    GREIMAS_FONTANILLE_1994 = SourceDocumentConfig(
        filename="Greimas, Fontanille 1994 Semiótica de las pasiones.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="Semiótica de las pasiones",
        author="Greimas y Fontanille",
        book="Semiótica de las pasiones",
        year="1994",
    )
    HONDERICH_2001 = SourceDocumentConfig(
        filename="Honderich 2001 Enciclopedia Oxford.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Enciclopedia Oxford",
        author="Honderich",
        book="Enciclopedia Oxford",
        year="2001",
    )
    LANGACKER_1987 = SourceDocumentConfig(
        filename="Langacker 1987 Fundations of Cognitive Grammar.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Fundations of Cognitive Grammar",
        author="Langacker",
        book="Fundations of Cognitive Grammar",
        year="1987",
    )
    LEECH_1997 = SourceDocumentConfig(
        filename="Leech 1997 Principios de pragmática.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="Principios de pragmática",
        author="Leech",
        book="Principios de pragmática",
        year="1997",
    )
    LEVINSON_1989 = SourceDocumentConfig(
        filename="Levinson 1989 Pragmática.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Pragmática",
        author="Levinson",
        book="Pragmática",
        year="1989",
    )
    LEVINSON_2004 = SourceDocumentConfig(
        filename="Levinson 2004 Significados presumibles.odt",
        split_pattern=LEVINSON_2004_PATTERN,
        title="Significados presumibles",
        author="Levinson",
        book="Significados presumibles",
        year="2004",
    )
    LYONS_1997 = SourceDocumentConfig(
        filename="Lyons 1997 Semántica lingüística.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Semántica lingüística",
        author="Lyons",
        book="Semántica lingüística",
        year="1997",
    )
    MOESCHLER_REBOUL_2000 = SourceDocumentConfig(
        filename="Moeschler y Reboul 2000 Diccionario enciclopedico.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Diccionario enciclopedico",
        author="Moeschler y Reboul",
        book="Diccionario enciclopedico",
        year="2000",
    )
    MORENTE_1983 = SourceDocumentConfig(
        filename="Morente 1983 Lecciones preliminares de filosofía.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Lecciones preliminares de filosofía",
        author="Morente",
        book="Lecciones preliminares de filosofía",
        year="1983",
    )
    PUTNAM_1988 = SourceDocumentConfig(
        filename="Putnam 1988 Razón, verdad e historia.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Razón, verdad e historia",
        author="Putnam",
        book="Razón, verdad e historia",
        year="1988",
    )
    PUTNAM_1990 = SourceDocumentConfig(
        filename="Putnam 1990 Representación y realidad.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Representación y realidad",
        author="Putnam",
        book="Representación y realidad",
        year="1990",
    )
    PUTNAM_1994 = SourceDocumentConfig(
        filename="Putnam 1994 Las mil caras del realismo.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Las mil caras del realismo",
        author="Putnam",
        book="Las mil caras del realismo",
        year="1994",
    )
    PUTNAM_1999 = SourceDocumentConfig(
        filename="Putnam 1999 El pragmatismo.odt",
        split_pattern=PAGE_DOT_PATTERN,
        title="El pragmatismo",
        author="Putnam",
        book="El pragmatismo",
        year="1999",
    )
    PUTNAM_2001 = SourceDocumentConfig(
        filename="Putnam 2001 La trenza de los tres cabos.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="La trenza de los tres cabos",
        author="Putnam",
        book="La trenza de los tres cabos",
        year="2001",
    )
    RORTY_1990 = SourceDocumentConfig(
        filename="Rorty 1990 El giro lingüístico.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="El giro lingüístico",
        author="Rorty",
        book="El giro lingüístico",
        year="1990",
    )
    RORTY_1991 = SourceDocumentConfig(
        filename="Rorty 1991 Contigengencia, ironía y solidaridad.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Contigengencia, ironía y solidaridad",
        author="Rorty",
        book="Contigengencia, ironía y solidaridad",
        year="1991",
    )
    STRAWSON_1997 = SourceDocumentConfig(
        filename="Strawson 1997 Análisis y metafísica.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Análisis y metafísica",
        author="Strawson",
        book="Análisis y metafísica",
        year="1997",
    )
    TED_HONDERICH_2001 = SourceDocumentConfig(
        filename="Ted Honderich 2001 Enciclopedia Oxford.odt",
        split_pattern=PARENTHESIS_YEAR_PAGE_PATTERN,
        title="Enciclopedia Oxford",
        author="Ted Honderich",
        book="Enciclopedia Oxford",
        year="2001",
    )
    WARNOCK_1989 = SourceDocumentConfig(
        filename="Warnock 1989 J.L. Austin.odt",
        split_pattern=WARNOCK_PAGE_PATTERN,
        title="J.L. Austin",
        author="Warnock",
        book="J.L. Austin",
        year="1989",
    )


def find_source_configs(source_dir: Path) -> list[tuple[SourceDocumentConfig, Path]]:
    configs = []
    for document in SourceDocument:
        source_path = source_dir / document.value.filename
        if source_path.exists():
            configs.append((document.value, source_path))
        else:
            raise FileNotFoundError(f"Expected source file not found: {source_path}")
    return configs
