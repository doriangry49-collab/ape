import platform

from ape.services.system_info_service import SystemInfoService


def test_system_info_service_provides_accurate_status():
    service = SystemInfoService()
    status = service.status

    assert isinstance(status, dict)
    assert status["package"] == "ape"
    assert status["python"] == platform.python_version()
    assert status["platform"] == platform.platform()


def test_system_info_service_collect_system_info_matches_status():
    service = SystemInfoService()
    assert service.collect_system_info() == service.status
