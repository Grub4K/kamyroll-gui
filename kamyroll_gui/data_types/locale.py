from enum import Enum



class Locale(Enum):
    """Represents a Locale."""
    #: Explicitly no locale
    NONE = ""
    #: Unknown locale
    UNDEFINED = "und"
    ENGLISH_US = "en-US"
    PORTUGUESE_BR = "pt-BR"
    PORTUGUESE_PT = "pt-PT"
    SPANISH_419 = "es-419"
    SPANISH_ES = "es-ES"
    FRENCH_FR = "fr-FR"
    ARABIC_ME = "ar-ME"
    ARABIC_SA = "ar-SA"
    ITALIAN_IT = "it-IT"
    GERMAN_DE = "de-DE"
    RUSSIAN_RU = "ru-RU"
    TURKISH_TR = "tr-TR"
    JAPANESE_JP = "ja-JP"
    CHINESE_CN = "zh-CN"

    def to_iso_639_2(self, /):
        """Get the ISO-639-2 language code."""
        return _TO_ISO_639_2[self]

    def __str__(self, /):
        """Get the clear name for a locale"""
        return _TO_CLEAR_NAME[self]

    def __repr__(self, /):
        return f'<{self.__class__.__name__}.{self.name}>'

_TO_CLEAR_NAME = {
    Locale.NONE: "None",
    Locale.UNDEFINED: "Undefined",
    Locale.ENGLISH_US: "English (USA)",
    Locale.PORTUGUESE_BR: "Portuguese (Brazil)",
    Locale.PORTUGUESE_PT: "Portuguese (Portugal)",
    Locale.SPANISH_419: "Spanish (Latinoamerica)",
    Locale.SPANISH_ES: "Spanish (Spain)",
    Locale.FRENCH_FR: "French",
    Locale.ARABIC_ME: "Arabic (Montenegro)",
    Locale.ARABIC_SA: "Arabic (Saudi Arabia)",
    Locale.ITALIAN_IT: "Italian",
    Locale.GERMAN_DE: "German",
    Locale.RUSSIAN_RU: "Russian",
    Locale.TURKISH_TR: "Turkish",
    Locale.JAPANESE_JP: "Japanese",
    Locale.CHINESE_CN: "Chinese",
}

_TO_ISO_639_2 = {
    Locale.NONE: "",
    Locale.ENGLISH_US: "eng",
    Locale.PORTUGUESE_BR: "por",
    Locale.PORTUGUESE_PT: "por",
    Locale.SPANISH_419: "spa",
    Locale.SPANISH_ES: "spa",
    Locale.FRENCH_FR: "fra",
    Locale.ARABIC_ME: "ara",
    Locale.ARABIC_SA: "ara",
    Locale.ITALIAN_IT: "ita",
    Locale.GERMAN_DE: "deu",
    Locale.RUSSIAN_RU: "rus",
    Locale.TURKISH_TR: "tur",
    Locale.JAPANESE_JP: "jpn",
    Locale.CHINESE_CN: "zho",
}
