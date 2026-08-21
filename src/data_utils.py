import pandas as pd


def first_address_word_counts(addresses: pd.Series) -> pd.Series:
    """Return counts grouped by the first whitespace-separated address word."""
    return (
        addresses.astype("string")
        .str.strip()
        .str.split()
        .str[0]
        .fillna("주소 없음")
        .value_counts()
    )
