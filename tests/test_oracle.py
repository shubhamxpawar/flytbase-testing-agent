from agentic_testing.oracle import normalize_device


def test_device_normalization_accepts_common_field_aliases() -> None:
    device = normalize_device(
        {"id": "drone-1", "online": True, "lat": "19.076", "lon": 72.8777, "stream_id": "stream-1"}
    )
    assert device.device_id == "drone-1"
    assert device.connected is True
    assert device.latitude == 19.076
    assert device.stream_identity == "stream-1"
