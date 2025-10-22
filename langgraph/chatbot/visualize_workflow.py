#!/usr/bin/env python3
"""
LangGraph 워크플로우 시각화 스크립트
실제 워크플로우 구조를 이미지로 생성합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import ChatbotApplication


def visualize_workflow():
    """워크플로우를 시각화하고 이미지로 저장"""
    try:
        # 챗봇 애플리케이션 초기화
        print("🚀 챗봇 애플리케이션 초기화 중...")
        app = ChatbotApplication(debug_mode=False)

        # 워크플로우 그래프 가져오기
        print("📊 워크플로우 그래프 생성 중...")
        graph = app.app.get_graph()

        # Mermaid PNG 이미지 생성
        print("🎨 Mermaid 이미지 생성 중...")
        mermaid_image = graph.draw_mermaid_png()

        # 이미지 저장
        output_dir = Path("workflow_images")
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / "langgraph_workflow.png"
        with open(output_path, "wb") as f:
            f.write(mermaid_image)

        print(f"✅ 워크플로우 이미지 저장 완료: {output_path}")
        print(f"📁 파일 크기: {len(mermaid_image)} bytes")

        return output_path

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def visualize_with_jupyter():
    """Jupyter 노트북에서 사용할 수 있는 시각화 함수"""
    try:
        from IPython.display import Image, display

        # 챗봇 애플리케이션 초기화
        app = ChatbotApplication(debug_mode=False)

        # 워크플로우 그래프 가져오기
        graph = app.app.get_graph()

        # Mermaid PNG 이미지 생성
        mermaid_image = graph.draw_mermaid_png()

        # Jupyter에서 이미지 표시
        display(Image(mermaid_image))

        return mermaid_image

    except ImportError:
        print("❌ IPython이 설치되지 않았습니다. pip install ipython을 실행하세요.")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 LangGraph 워크플로우 시각화")
    print("=" * 60)

    # 이미지 파일로 저장
    result = visualize_workflow()

    if result:
        print(f"\n📋 사용 방법:")
        print(f"1. 생성된 이미지: {result}")
        print(f"2. Jupyter 노트북에서 사용:")
        print(f"   from visualize_workflow import visualize_with_jupyter")
        print(f"   visualize_with_jupyter()")
        print(f"3. 또는 직접 코드 실행:")
        print(f"   from IPython.display import Image, display")
        print(f"   from app import ChatbotApplication")
        print(f"   app = ChatbotApplication()")
        print(f"   subgraph_image = app.app.get_graph().draw_mermaid_png()")
        print(f"   display(Image(subgraph_image))")
    else:
        print("❌ 시각화 실패")
        sys.exit(1)
