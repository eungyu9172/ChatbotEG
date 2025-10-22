import os
import sys
import json
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any

from langgraph.graph import StateGraph, END

from config import LOGGING_CONFIG
from states import ChatState
from nodes.validate_input import validate_input
from nodes.check_simple import check_simple_query
from nodes.direct_answer import direct_answer
from nodes.rewrite_query import rewrite_query
from nodes.retrieve import retrieve
from nodes.rerank import rerank
from nodes.check_answerable import check_answerability
from nodes.generate import generate_answer
from nodes.ask_info import ask_for_more_info
from nodes.force_final_answer import force_final_answer
from routers import (
    input_valid_router, check_simple_router, check_answerable_router,
    should_continue, tools_router
)
from utils.llm_clients import tool_node
from utils.logger import logger, session_logger
from tools import AVAILABLE_TOOLS


class ChatbotApplication:
    """메인 챗봇 애플리케이션 클래스"""

    def __init__(self, debug_mode: bool = None):
        """
        애플리케이션 초기화

        Args:
            debug_mode: 디버그 모드 활성화 여부
        """
        self.debug_mode = debug_mode if debug_mode is not None else LOGGING_CONFIG["debug_mode"]
        self.app = None
        self.session_stats = {}

        # 세션 로그 시작
        session_logger.start_session()

        logger.info("🚀 ChatBot Application 초기화 시작")
        logger.info(f"디버그 모드: {'ON' if self.debug_mode else 'OFF'}")
        logger.info(f"사용 가능한 도구: {[tool.name for tool in AVAILABLE_TOOLS]}")

        self._validate_environment()
        self._create_workflow()

    def _validate_environment(self):
        """환경 설정 검증"""
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            raise ValueError("OPENAI_API_KEY environment variable is required")

        logger.info("✅ 환경 설정 검증 완료")

    def _create_workflow(self):
        """워크플로우 생성 및 컴파일"""
        logger.info("📊 워크플로우 생성 시작")

        try:
            workflow = StateGraph(ChatState)

            # 노드 추가
            self._add_nodes(workflow)

            # 엣지 및 라우팅 설정
            self._configure_routing(workflow)

            # 워크플로우 컴파일
            self.app = workflow.compile()

            logger.info("✅ 워크플로우 생성 완료")

        except Exception as e:
            logger.error(f"❌ 워크플로우 생성 실패: {e}", exc_info=True)
            raise

    def _add_nodes(self, workflow: StateGraph):
        """모든 노드를 워크플로우에 추가"""
        nodes = {
            "validate_input": validate_input,
            "check_simple": check_simple_query,
            "direct_answer": direct_answer,
            "tools": tool_node,
            "rewrite": rewrite_query,
            "retrieve": retrieve,
            "rerank": rerank,
            "check_answerable": check_answerability,
            "generate": generate_answer,
            "ask_info": ask_for_more_info,
            "force_final_answer": force_final_answer
        }

        for name, func in nodes.items():
            workflow.add_node(name, func)
            logger.debug(f"노드 추가: {name}")

    def _configure_routing(self, workflow: StateGraph):
        """라우팅 설정"""
        # 엔트리 포인트 설정
        workflow.set_entry_point("validate_input")

        # 조건부 엣지 설정
        workflow.add_conditional_edges(
            "validate_input",
            input_valid_router,
            {
                "check_simple": "check_simple",
                "error": END
            }
        )

        workflow.add_conditional_edges(
            "check_simple",
            check_simple_router,
            {
                "direct_answer": "direct_answer",
                "rewrite": "rewrite"
            }
        )

        workflow.add_conditional_edges(
            "direct_answer",
            should_continue,
            ["tools", "force_final_answer", END]
        )

        workflow.add_conditional_edges(
            "check_answerable",
            check_answerable_router,
            {
                "generate": "generate",
                "ask_info": "ask_info"
            }
        )

        workflow.add_conditional_edges(
            "generate",
            should_continue,
            ["tools", "force_final_answer", END]
        )

        workflow.add_conditional_edges(
            "tools",
            tools_router,
            {
                "direct_answer": "direct_answer",
                "generate": "generate"
            }
        )

        # 단순 엣지 설정
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "check_answerable")
        workflow.add_edge("ask_info", END)
        workflow.add_edge("force_final_answer", END)

        logger.debug("라우팅 설정 완료")

    def process_query(
        self,
        user_query: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        단일 쿼리 처리

        Args:
            user_query: 사용자 질문
            session_id: 세션 ID (선택사항)

        Returns:
            처리 결과 딕셔너리
        """
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🔍 쿼리 처리 시작 [세션: {session_id}]")
        logger.info(f"질문: {user_query}")

        # 초기 상태 생성
        initial_state = {
            "session_id": session_id,
            "user_query": user_query,
            "messages": self.session_stats.get(session_id, {}).get("messages", []),
            "processing_stage": "start",
            "tool_call_count": 0,
            "max_tool_calls": 3,
            "error": None,
            "is_simple_query": None,
            "rewritten_query": None,
            "retrieve_results": None,
            "reranked_context": None,
            "is_answerable": None,
            "final_answer": None,
            "confidence_score": None
        }

        start_time = time.time()

        try:
            # 워크플로우 실행
            final_state = self.app.invoke(initial_state)

            execution_time = time.time() - start_time

            # 결과 처리
            result = self._process_result(final_state, execution_time, session_id)

            # 세션 상태 업데이트
            self._update_session_stats(session_id, final_state, execution_time)

            logger.info(f"✅ 쿼리 처리 완료 ({execution_time:.2f}초)")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 쿼리 처리 실패 ({execution_time:.2f}초): {e}", exc_info=True)

            return {
                "session_id": session_id,
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "final_answer": "죄송합니다. 처리 중 오류가 발생했습니다.",
                "debug_info": traceback.format_exc() if self.debug_mode else None
            }

    def _process_result(
        self,
        final_state: Dict[str, Any],
        execution_time: float,
        session_id: str
    ) -> Dict[str, Any]:
        """처리 결과 가공"""
        final_answer = final_state.get("final_answer", "답변을 생성할 수 없습니다.")
        processing_stage = final_state.get("processing_stage", "unknown")

        # 토큰 사용량 계산
        input_tokens = final_state.get("input_token_count", 0)
        response_tokens = final_state.get("response_tokens", 0)

        result = {
            "session_id": session_id,
            "success": not bool(final_state.get("error")),
            "final_answer": final_answer,
            "confidence_score": final_state.get("confidence_score"),
            "processing_stage": processing_stage,
            "execution_time": execution_time,
            "token_usage": {
                "input_tokens": input_tokens,
                "response_tokens": response_tokens,
                "total_tokens": input_tokens + response_tokens
            },
            "metadata": {
                "is_simple_query": final_state.get("is_simple_query"),
                "rewritten_query": final_state.get("rewritten_query"),
                "retrieval_time": final_state.get("retrieval_time", 0)
            }
        }

        # 디버그 정보 추가
        if self.debug_mode:
            result["debug_info"] = {
                "full_state": final_state,
                "message_count": len(final_state.get("messages") or []),
                "context_count": len(final_state.get("reranked_context") or []),
                "error": final_state.get("error")
            }

        return result

    def _update_session_stats(
        self,
        session_id: str,
        final_state: Dict[str, Any],
        execution_time: float
    ):
        """세션 통계 업데이트"""
        if session_id not in self.session_stats:
            self.session_stats[session_id] = {
                "created_at": datetime.now(),
                "query_count": 0,
                "total_execution_time": 0,
                "messages": []
            }

        stats = self.session_stats[session_id]
        stats["query_count"] += 1
        stats["total_execution_time"] += execution_time
        stats["last_activity"] = datetime.now()
        stats["messages"] = final_state.get("messages", [])

    def interactive_chat(self):
        """대화형 채팅 모드"""
        logger.info("💬 대화형 채팅 모드 시작")
        print("\n" + "=" * 60)
        print("🤖 AI 챗봇과 대화를 시작합니다!")
        print("💡 명령어:")
        print("  - 'quit', 'exit', 'q': 종료")
        print("  - 'clear': 대화 히스토리 초기화")
        print("  - 'stats': 세션 통계 보기")
        print("  - 'debug on/off': 디버그 모드 전환")
        print("  - 'help': 도움말")
        print("=" * 60)

        session_id = f"interactive_{datetime.now().strftime('%H%M%S')}"

        while True:
            try:
                user_input = input("\n🧑 사용자: ").strip()

                # 명령어 처리
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 대화를 종료합니다. 감사합니다!")
                    # 세션 로그 종료
                    session_logger.end_session()
                    break

                elif user_input.lower() == 'clear':
                    if session_id in self.session_stats:
                        self.session_stats[session_id]["messages"] = []
                    print("🗑️ 대화 히스토리가 초기화되었습니다.")
                    continue

                elif user_input.lower() == 'stats':
                    self._show_session_stats(session_id)
                    continue

                elif user_input.lower().startswith('debug '):
                    mode = user_input.lower().split()[1]
                    if mode == 'on':
                        self.debug_mode = True
                        print("🔍 디버그 모드가 활성화되었습니다.")
                    elif mode == 'off':
                        self.debug_mode = False
                        print("🔍 디버그 모드가 비활성화되었습니다.")
                    continue

                elif user_input.lower() == 'help':
                    self._show_help()
                    continue

                elif not user_input:
                    print("❓ 질문을 입력해주세요.")
                    continue

                # 쿼리 처리
                print("🤔 처리 중...")
                result = self.process_query(user_input, session_id)

                # 결과 출력
                print(f"\n🤖 AI: {result['final_answer']}")

                # 디버그 정보 출력
                if self.debug_mode and result.get('debug_info'):
                    self._show_debug_info(result)

            except KeyboardInterrupt:
                print("\n\n⚠️ 중단되었습니다. 'quit'을 입력해 정상 종료하세요.")
            except Exception as e:
                logger.error(f"대화형 모드 오류: {e}", exc_info=True)
                print(f"❌ 오류가 발생했습니다: {e}")

    def _show_session_stats(self, session_id: str):
        """세션 통계 표시"""
        if session_id not in self.session_stats:
            print("📊 아직 통계 데이터가 없습니다.")
            return

        stats = self.session_stats[session_id]
        avg_time = stats["total_execution_time"] / stats["query_count"] if stats["query_count"] > 0 else 0

        print(f"\n📊 세션 통계 [{session_id}]")
        print(f"  • 질문 수: {stats['query_count']}개")
        print(f"  • 총 실행 시간: {stats['total_execution_time']:.2f}초")
        print(f"  • 평균 응답 시간: {avg_time:.2f}초")
        print(f"  • 메시지 수: {len(stats['messages'])}개")
        print(f"  • 마지막 활동: {stats.get('last_activity', 'N/A')}")

    def _show_debug_info(self, result: Dict[str, Any]):
        """디버그 정보 표시"""
        print("\n🔍 디버그 정보:")
        print(f"  • 처리 단계: {result['processing_stage']}")
        print(f"  • 실행 시간: {result['execution_time']:.3f}초")
        # print(f"  • 신뢰도: {result['confidence_score']:.2f}")
        print(f"  • 토큰 사용량: {result['token_usage']['total_tokens']}")

        if result['metadata']['rewritten_query']:
            print(f"  • 재작성된 쿼리: {result['metadata']['rewritten_query']}")

        # if result['metadata']['search_keywords']:
        #     print(f"  • 검색 키워드: {result['metadata']['search_keywords']}")

    def _show_help(self):
        """도움말 표시"""
        print("""
📋 사용 가능한 명령어:

기본 명령:
  • quit/exit/q     - 채팅 종료
  • clear           - 대화 히스토리 초기화
  • stats           - 현재 세션 통계 보기
  • help            - 이 도움말 표시

디버그 명령:
  • debug on        - 디버그 정보 표시 활성화
  • debug off       - 디버그 정보 표시 비활성화

사용 가능한 도구:
  • 현재 시간 조회
  • 주식 가격 조회
  • 날씨 정보 조회

예시 질문:
  • "지금 몇 시야?"
  • "AAPL 주가 알려줘"
  • "서울 날씨 어때?"
  • "파이썬이란 무엇인가요?"
""")

    def benchmark_test(
        self,
        test_queries: List[str],
        iterations: int = 3
    ) -> Dict[str, Any]:
        """벤치마크 테스트 실행"""
        logger.info(f"🏃 벤치마크 테스트 시작: {len(test_queries)}개 쿼리, {iterations}회 반복")

        results = []
        total_start_time = time.time()

        for i, query in enumerate(test_queries, 1):
            logger.info(f"[{i}/{len(test_queries)}] 테스트 쿼리: {query}")

            query_results = []

            for iteration in range(iterations):
                session_id = f"benchmark_{i}_{iteration}"
                result = self.process_query(query, session_id)

                query_results.append({
                    "iteration": iteration + 1,
                    "success": result["success"],
                    "execution_time": result["execution_time"],
                    "token_usage": result["token_usage"]["total_tokens"],
                    "processing_stage": result["processing_stage"]
                })

            # 통계 계산
            successful_runs = [r for r in query_results if r["success"]]
            if successful_runs:
                avg_time = sum(r["execution_time"] for r in successful_runs) / len(successful_runs)
                avg_tokens = sum(r["token_usage"] for r in successful_runs) / len(successful_runs)
                success_rate = len(successful_runs) / iterations
            else:
                avg_time = 0
                avg_tokens = 0
                success_rate = 0

            results.append({
                "query": query,
                "iterations": query_results,
                "statistics": {
                    "success_rate": success_rate,
                    "avg_execution_time": avg_time,
                    "avg_token_usage": avg_tokens,
                    "total_runs": iterations,
                    "successful_runs": len(successful_runs)
                }
            })

            logger.info(f"  성공률: {success_rate:.1%}, 평균 시간: {avg_time:.2f}초")

        total_time = time.time() - total_start_time

        benchmark_result = {
            "test_info": {
                "total_queries": len(test_queries),
                "iterations_per_query": iterations,
                "total_execution_time": total_time,
                "timestamp": datetime.now().isoformat()
            },
            "results": results,
            "overall_stats": {
                "total_success_rate": sum(r["statistics"]["success_rate"] for r in results) / len(results),
                "avg_execution_time": sum(r["statistics"]["avg_execution_time"] for r in results) / len(results),
                "avg_token_usage": sum(r["statistics"]["avg_token_usage"] for r in results) / len(results)
            }
        }

        logger.info(f"✅ 벤치마크 테스트 완료 ({total_time:.2f}초)")

        return benchmark_result


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="LangGraph AI 챗봇")
    parser.add_argument(
        "--mode",
        choices=["chat", "test", "benchmark"],
        default="chat",
        help="실행 모드 선택"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="단일 쿼리 테스트"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 모드 활성화"
    )
    parser.add_argument(
        "--benchmark-queries",
        nargs="+",
        default=["안녕하세요", "지금 몇 시야?", "AAPL 주가 알려줘", "지금 서울 날씨를 알려줘"],
        help="벤치마크 테스트 쿼리들"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="벤치마크 반복 횟수"
    )

    args = parser.parse_args()

    try:
        # 애플리케이션 초기화
        app = ChatbotApplication(debug_mode=args.debug)

        if args.mode == "chat":
            # 대화형 모드
            app.interactive_chat()

        elif args.mode == "test":
            # 단일 쿼리 테스트
            query = args.query or "안녕하세요!"
            result = app.process_query(query)

            print(f"\n질문: {query}")
            print(f"답변: {result['final_answer']}")
            print(f"처리 시간: {result['execution_time']:.3f}초")
            print(f"성공 여부: {'✅' if result['success'] else '❌'}")

        elif args.mode == "benchmark":
            # 벤치마크 모드
            benchmark_result = app.benchmark_test(args.benchmark_queries, args.iterations)

            # 결과 저장
            output_file = f"benchmark_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(benchmark_result, f, ensure_ascii=False, indent=2, default=str)

            print("\n📊 벤치마크 결과:")
            print(f"  총 성공률: {benchmark_result['overall_stats']['total_success_rate']:.1%}")
            print(f"  평균 실행 시간: {benchmark_result['overall_stats']['avg_execution_time']:.2f}초")
            print(f"  평균 토큰 사용량: {benchmark_result['overall_stats']['avg_token_usage']:.0f}")
            print(f"  결과 저장됨: {output_file}")

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        print("\n👋 프로그램을 종료합니다.")
        session_logger.end_session()
    except Exception as e:
        logger.error(f"애플리케이션 실행 오류: {e}", exc_info=True)
        print(f"❌ 오류: {e}")
        session_logger.end_session()
        sys.exit(1)


if __name__ == "__main__":
    main()
