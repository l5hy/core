"""Constants for the Google Translate text-to-speech integration."""
from dataclasses import dataclass

CONF_TLD = "tld"
DEFAULT_LANG = "en"
DEFAULT_TLD = "com"
DOMAIN = "google_translate"
CO_UK = "co.uk"

SUPPORT_LANGUAGES = [
    "af",
    "ar",
    "bg",
    "bn",
    "bs",
    "ca",
    "cs",
    "cy",
    "da",
    "de",
    "el",
    "en",
    "eo",
    "es",
    "et",
    "fi",
    "fr",
    "gu",
    "hi",
    "hr",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "iw",
    "ja",
    "jw",
    "km",
    "kn",
    "ko",
    "la",
    "lv",
    "lt",
    "mk",
    "ml",
    "mr",
    "my",
    "ne",
    "nl",
    "no",
    "pl",
    "pt",
    "ro",
    "ru",
    "si",
    "sk",
    "sq",
    "sr",
    "su",
    "sv",
    "sw",
    "ta",
    "te",
    "th",
    "tl",
    "tr",
    "uk",
    "ur",
    "vi",
    # dialects
    "zh-CN",
    "zh-cn",
    "zh-tw",
    "en-us",
    "en-ca",
    "en-uk",
    "en-gb",
    "en-au",
    "en-gh",
    "en-in",
    "en-ie",
    "en-nz",
    "en-ng",
    "en-ph",
    "en-za",
    "en-tz",
    "fr-ca",
    "fr-fr",
    "pt-br",
    "pt-pt",
    "es-es",
    "es-us",
]

SUPPORT_TLD = [
    "com",
    "ad",
    "ae",
    "com.af",
    "com.ag",
    "com.ai",
    "al",
    "am",
    "co.ao",
    "com.ar",
    "as",
    "at",
    "com.au",
    "az",
    "ba",
    "com.bd",
    "be",
    "bf",
    "bg",
    "com.bh",
    "bi",
    "bj",
    "com.bn",
    "com.bo",
    "com.br",
    "bs",
    "bt",
    "co.bw",
    "by",
    "com.bz",
    "ca",
    "cd",
    "cf",
    "cg",
    "ch",
    "ci",
    "co.ck",
    "cl",
    "cm",
    "cn",
    "com.co",
    "co.cr",
    "com.cu",
    "cv",
    "com.cy",
    "cz",
    "de",
    "dj",
    "dk",
    "dm",
    "com.do",
    "dz",
    "com.ec",
    "ee",
    "com.eg",
    "es",
    "com.et",
    "fi",
    "com.fj",
    "fm",
    "fr",
    "ga",
    "ge",
    "gg",
    "com.gh",
    "com.gi",
    "gl",
    "gm",
    "gr",
    "com.gt",
    "gy",
    "com.hk",
    "hn",
    "hr",
    "ht",
    "hu",
    "co.id",
    "ie",
    "co.il",
    "im",
    "co.in",
    "iq",
    "is",
    "it",
    "je",
    "com.jm",
    "jo",
    "co.jp",
    "co.ke",
    "com.kh",
    "ki",
    "kg",
    "co.kr",
    "com.kw",
    "kz",
    "la",
    "com.lb",
    "li",
    "lk",
    "co.ls",
    "lt",
    "lu",
    "lv",
    "com.ly",
    "co.ma",
    "md",
    "me",
    "mg",
    "mk",
    "ml",
    "com.mm",
    "mn",
    "ms",
    "com.mt",
    "mu",
    "mv",
    "mw",
    "com.mx",
    "com.my",
    "co.mz",
    "com.na",
    "com.ng",
    "com.ni",
    "ne",
    "nl",
    "no",
    "com.np",
    "nr",
    "nu",
    "co.nz",
    "com.om",
    "com.pa",
    "com.pe",
    "com.pg",
    "com.ph",
    "com.pk",
    "pl",
    "pn",
    "com.pr",
    "ps",
    "pt",
    "com.py",
    "com.qa",
    "ro",
    "ru",
    "rw",
    "com.sa",
    "com.sb",
    "sc",
    "se",
    "com.sg",
    "sh",
    "si",
    "sk",
    "com.sl",
    "sn",
    "so",
    "sm",
    "sr",
    "st",
    "com.sv",
    "td",
    "tg",
    "co.th",
    "com.tj",
    "tl",
    "tm",
    "tn",
    "to",
    "com.tr",
    "tt",
    "com.tw",
    "co.tz",
    "com.ua",
    "co.ug",
    CO_UK,
    "com.uy",
    "co.uz",
    "com.vc",
    "co.ve",
    "vg",
    "co.vi",
    "com.vn",
    "vu",
    "ws",
    "rs",
    "co.za",
    "co.zm",
    "co.zw",
    "cat",
]


@dataclass
class Dialect:
    """Language and TLD for a dialect supported by Google Translate."""

    lang: str
    tld: str


MAP_LANG_TLD: dict[str, Dialect] = {
    "en-us": Dialect("en", "com"),
    "en-gb": Dialect("en", CO_UK),
    "en-uk": Dialect("en", CO_UK),
    "en-au": Dialect("en", "com.au"),
    "en-ca": Dialect("en", "ca"),
    "en-in": Dialect("en", "co.in"),
    "en-ie": Dialect("en", "ie"),
    "en-za": Dialect("en", "co.za"),
    "fr-ca": Dialect("fr", "ca"),
    "fr-fr": Dialect("fr", "fr"),
    "pt-br": Dialect("pt", "com.br"),
    "pt-pt": Dialect("pt", "pt"),
    "es-es": Dialect("es", "es"),
    "es-us": Dialect("es", "com"),
}
