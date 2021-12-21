import pkg_resources


def is_this_version_smaller(lib_name: str, version_check: str) -> bool:
    return pkg_resources.parse_version(
            pkg_resources.get_distribution(lib_name).version) < \
            pkg_resources.parse_version(version_check)
