from PySide6.QtCore import QSettings


class AppSettings:
    _qsettings = None

    @classmethod
    def _q(cls) -> QSettings:
        if cls._qsettings is None:
            cls._qsettings = QSettings()
        return cls._qsettings

    @classmethod
    def get(cls, key: str, default, cast=None):
        value = cls._q().value(key, default)
        if cast is not None:
            try:
                value = cast(value)
            except (TypeError, ValueError):
                value = default
        return value

    @classmethod
    def set(cls, key: str, value):
        cls._q().setValue(key, value)

    @classmethod
    def _get_bool(cls, key: str, default: bool) -> bool:
        return bool(cls._q().value(key, default, type=bool))

    @classmethod
    def _get_int(cls, key: str, default: int) -> int:
        try:
            return int(cls._q().value(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def _get_str(cls, key: str, default: str) -> str:
        value = cls._q().value(key, default)
        return str(value) if value is not None else default

    @classmethod
    def theme_name(cls) -> str:
        return cls._get_str("theme/name", "warm")

    @classmethod
    def set_theme_name(cls, value: str):
        cls.set("theme/name", value)

    @classmethod
    def bubble_size(cls) -> str:
        return cls._get_str("bubble/size", "medium")

    @classmethod
    def set_bubble_size(cls, value: str):
        cls.set("bubble/size", value)

    @classmethod
    def pet_size(cls) -> str:
        return cls._get_str("pet/size", "medium")

    @classmethod
    def set_pet_size(cls, value: str):
        cls.set("pet/size", value)

    @classmethod
    def pet_opacity(cls) -> int:
        return cls._get_int("pet/opacity", 100)

    @classmethod
    def set_pet_opacity(cls, value: int):
        cls.set("pet/opacity", int(value))

    @classmethod
    def hidden(cls) -> bool:
        return cls._get_bool("pet/hidden", False)

    @classmethod
    def set_hidden(cls, value: bool):
        cls.set("pet/hidden", bool(value))

    @classmethod
    def muted(cls) -> bool:
        return cls._get_bool("sound/muted", False)

    @classmethod
    def set_muted(cls, value: bool):
        cls.set("sound/muted", bool(value))

    @classmethod
    def font_family(cls) -> str:
        return cls._get_str("font/family", "")

    @classmethod
    def set_font_family(cls, value: str):
        cls.set("font/family", value)

    @classmethod
    def font_size(cls) -> int:
        return cls._get_int("font/size", 10)

    @classmethod
    def set_font_size(cls, value: int):
        cls.set("font/size", int(value))

    @classmethod
    def reminder_option(cls) -> int:
        return cls._get_int("reminder/option", 3)

    @classmethod
    def set_reminder_option(cls, value: int):
        cls.set("reminder/option", int(value))

    @classmethod
    def stand_reminder_enabled(cls) -> bool:
        return cls._get_bool("stand/enabled", False)

    @classmethod
    def set_stand_reminder_enabled(cls, value: bool):
        cls.set("stand/enabled", bool(value))

    @classmethod
    def stand_interval(cls) -> int:
        return cls._get_int("stand/interval", 45)

    @classmethod
    def set_stand_interval(cls, value: int):
        cls.set("stand/interval", int(value))
