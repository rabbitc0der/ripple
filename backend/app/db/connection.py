import time
from typing import Any, Dict, Optional
from falkordb import FalkorDB
from app.config import settings

class FalkorManager:
    def __init__(self):
        self.host = settings.FALKORDB_HOST
        self.port = settings.FALKORDB_PORT
        self.password = settings.FALKORDB_PASSWORD
        self._client: Optional[FalkorDB] = None

    @property
    def client(self) -> FalkorDB:
        if self._client is None:
            self.connect()
        return self._client

    def connect(self) -> FalkorDB:
        self._client = FalkorDB(
            host=self.host,
            port=self.port,
            password=self.password
        )
        return self._client

    def get_graph(self, graph_name: Optional[str] = None):
        target = graph_name or settings.DEFAULT_GRAPH
        return self.client.select_graph(target)

    def execute_raw(self, command: str, *args):
        """Execute raw Redis/FalkorDB commands (e.g. GRAPH.COPY, GRAPH.DELETE)."""
        return self.client.connection.execute_command(command, *args)

    def query_ro(self, graph_name: str, query: str, params: Optional[Dict[str, Any]] = None):
        """
        Execute read-only query using GRAPH.RO_QUERY for guaranteed read safety.
        """
        g = self.get_graph(graph_name)
        start = time.perf_counter()
        res = g.ro_query(query, params or {})
        duration_ms = (time.perf_counter() - start) * 1000.0
        return res, duration_ms

    def query(self, graph_name: str, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute standard read/write query."""
        g = self.get_graph(graph_name)
        start = time.perf_counter()
        res = g.query(query, params or {})
        duration_ms = (time.perf_counter() - start) * 1000.0
        return res, duration_ms

    def check_health(self) -> Dict[str, Any]:
        """Check if FalkorDB is reachable and measure roundtrip ping latency."""
        try:
            start = time.perf_counter()
            self.client.connection.ping()
            latency_ms = (time.perf_counter() - start) * 1000.0
            return {"status": "healthy", "latency_ms": round(latency_ms, 2)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

db_manager = FalkorManager()
