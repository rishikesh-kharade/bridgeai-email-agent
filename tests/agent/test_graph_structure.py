from app.agents.graph import build_graph
from tests.fakes import FakeEmailProvider
from tests.fakes import FakeTaskProvider


def test_graph_can_compile_without_client_data():
    graph = build_graph(
        FakeEmailProvider(),
        FakeTaskProvider(),
    )
    assert graph is not None
