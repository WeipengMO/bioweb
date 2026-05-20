from bioweb_analysis.results import cleanup_old_results


def cleanup_old_result_images(max_age_seconds: int = 24 * 60 * 60) -> int:
    """Purge result PNG files older than the given age.

    Delegates to the shared ``bioweb_analysis.results`` module so that the
    same logic is used everywhere (analysis code, CLI tools, and backend
    startup).
    """
    return cleanup_old_results(max_age_seconds=max_age_seconds)
