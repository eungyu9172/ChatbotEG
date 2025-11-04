from typing import Dict, List, Optional
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool


class MCPClientManager:
    """MCP 서버들을 관리하는 클라이언트 매니저"""

    def __init__(self):
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[BaseTool] = []
        self._initialized = False

    def _discover_servers(self) -> Dict:
        """
        mcp_servers 폴더에서 서버를 자동으로 탐색합니다.

        규칙:
        - mcp_servers/* 폴더 스캔
        - 각 폴더에 server.py가 있으면 서버로 인식
        """
        root_path = Path(__file__).parent.parent.parent
        servers_path = root_path / "mcp_servers"

        if not servers_path.exists():
            print(f"⚠️  MCP 서버 폴더를 찾을 수 없습니다: {servers_path}")
            return {}

        connections = {}

        print("🔍 MCP 서버 자동 탐색 중...")

        # 모든 하위 폴더 스캔
        for server_folder in servers_path.iterdir():
            if not server_folder.is_dir():
                continue

            # server.py 파일 확인
            server_file = server_folder / "server.py"
            if not server_file.exists():
                continue

            # 비활성화 체크 (.disabled 파일 존재 여부)
            if (server_folder / ".disabled").exists():
                print(f"   ⊘ {server_folder.name}: 비활성화됨 (.disabled 파일)")
                continue

            # 서버 등록
            server_name = server_folder.name
            connections[server_name] = {
                "command": sys.executable,
                "args": [str(server_file)],
                "transport": "stdio"
            }

            print(f"   ✓ {server_name}: {server_file}")

        return connections

    async def initialize(self):
        """MCP 서버를 자동으로 탐색하고 로드합니다."""
        print("🔧 MCP 자동 초기화 중...")

        # 서버 자동 탐색
        connections = self._discover_servers()

        if not connections:
            print("⚠️  탐색된 MCP 서버가 없습니다.")
            return []

        print(f"\n📡 {len(connections)}개 서버 발견됨")

        # MultiServerMCPClient 생성
        self.client = MultiServerMCPClient(connections)

        # 모든 도구 자동 로드
        self.tools = await self.client.get_tools()

        print(f"✅ MCP 초기화 완료: {len(self.tools)}개 도구 로드됨")
        for tool in self.tools:
            print(f"   - {tool.name}")

        return self.tools

    def get_tools(self):
        """로드된 모든 도구를 반환합니다."""
        return self.tools

    def is_initialized(self) -> bool:
        """초기화 여부를 반환합니다."""
        return self._initialized


_mcp_manager: Optional[MCPClientManager] = None


async def get_mcp_manager() -> MCPClientManager:
    """MCP Manager 싱글톤 인스턴스를 반환합니다."""
    global _mcp_manager

    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
        await _mcp_manager.initialize()

    return _mcp_manager
