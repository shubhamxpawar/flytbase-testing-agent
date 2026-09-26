from pathlib import Path

from agentic_testing.config import load_target


def test_flytbase_node_dev_profile_matches_verified_runtime_contract() -> None:
    target = load_target(Path("configs/flytbase-cockpit.yaml"))
    assert target.target_id == "flytbase-cockpit-node-dev"
    assert target.base_url == "http://localhost:5173"
    assert target.control_api_base_url == "http://localhost:4000/api"
    assert target.websocket_url == "http://localhost:4000"
    assert target.socket_transport == "socket.io"
    assert target.socket_namespace == "/"
    assert target.socket_org_id == "flytbase"
    assert target.whep_base_url == "http://localhost:8889"
    assert target.video_player_testid == "video-player"
    assert target.video_stream_payload_path == "video.url"
    assert target.map_position_epsilon_m == 0
    assert target.freshness_threshold_s == 5
