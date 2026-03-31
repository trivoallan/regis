"""regis — Docker Registry Analysis CLI."""

import warnings

warnings.filterwarnings(
    "ignore",
    message="urllib3 .* or chardet .*/charset_normalizer .* doesn't match a supported version!",
)
