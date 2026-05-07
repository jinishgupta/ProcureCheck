def assign_section(page_num, section_map):
    """
    Returns the section name for a given 0-based page number.

    section_map format (with ranges):
        { "section name": {"start": int, "end": int} }

    Falls back to the "last section whose start <= page_num" if no exact
    range match is found (handles documents where end pages aren't listed).
    """
    if not section_map:
        return "unknown"

    # Check for explicit range match first
    for section, bounds in section_map.items():
        if isinstance(bounds, dict):
            start = bounds.get("start", 0)
            end   = bounds.get("end", start)
            if start <= page_num <= end:
                return section
        else:
            # Legacy: plain int (start page only)
            if page_num == bounds:
                return section

    # Fallback: "most recent section whose start <= page_num"
    # (handles pages between sections where no explicit end was given)
    current = "unknown"
    sorted_sections = sorted(
        section_map.items(),
        key=lambda x: x[1]["start"] if isinstance(x[1], dict) else x[1]
    )
    for section, bounds in sorted_sections:
        start = bounds["start"] if isinstance(bounds, dict) else bounds
        if page_num >= start:
            current = section
        else:
            break

    return current
