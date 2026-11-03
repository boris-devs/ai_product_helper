RECOMMENDED_SPECS: dict[str, tuple[str, ...]] = {
    "диапазон измерений": ("диапазон", "предел измерени"),
    "класс точности / погрешность": ("класс точности", "точност", "погрешност"),
    "питание": ("питани", "напряжение питания"),
    "корпус": ("корпус",),
    "присоединение к процессу": ("присоединени", "резьб", "штуцер"),
    "интерфейсы / выходной сигнал": ("интерфейс", "выходной сигнал", "протокол"),
    "степень защиты": ("защит", "ip"),
}

NO_DATA = "данных нет"


def find_spec_group(spec_name: str) -> str | None:
    normalized = spec_name.lower()
    for group, aliases in RECOMMENDED_SPECS.items():
        if any(alias in normalized for alias in aliases):
            return group
    return None
