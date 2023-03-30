UI_ELEMENT_ID_PREFIX = "sddp-"


def make_element_id(name: str) -> str:
    return UI_ELEMENT_ID_PREFIX + name
