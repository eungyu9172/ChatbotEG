# LangGraph 챗봇 시스템

LangGraph를 활용한 지능형 챗봇 시스템과 RAG 문서 처리 시스템입니다. 도구(Tools)를 활용한 실시간 정보 조회와 RAG(Retrieval-Augmented Generation) 기능을 지원합니다.

## 🚀 주요 기능

### 챗봇 시스템 (chatbot/)
- **지능형 라우팅**: 단순 질문과 복잡한 질문을 자동으로 구분하여 처리
- **도구 시스템**: 시간 조회, 주식 가격, 날씨 정보 등 (추가 기능 개발 예정)
- **세션 관리**: 대화 히스토리 유지 및 세션별 로그 관리
- **안전장치**: Tool 호출 횟수 제한으로 무한 루프 방지
- **RAG 통합**: 벡터 검색 기반 문서 검색 시스템

### RAG 문서 처리 시스템 (rag_ingest/)
- **다양한 문서 형식 지원**: PDF, TXT 등 다양한 형식의 문서 처리
- **문서 청킹**: 효율적인 검색을 위한 문서 분할
- **벡터 임베딩**: ChromaDB를 활용한 벡터 저장소 구축
- **문서 인덱싱**: 빠른 검색을 위한 문서 인덱싱 시스템

## 📋 요구사항

- Python 3.8+
- OpenAI API Key (챗봇 시스템용)
- ChromaDB (RAG 시스템용)
- 필요한 패키지들 (각 폴더의 requirements.txt 참조)

## ⚙️ 로컬 설치 및 설정

### 챗봇 시스템 설정

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd langgraph/chatbot
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정**
   ```bash
   # .env 파일 생성
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   echo "DEBUG_MODE=true" >> .env
   ```

### RAG 문서 처리 시스템 설정

1. **RAG 시스템 폴더로 이동**
   ```bash
   cd langgraph/rag_ingest
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정**
   ```bash
   # .env 파일 생성 (필요시)
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## 🎯 사용 방법

### 챗봇 시스템 사용법

1. **대화형 모드 (기본)**
   ```bash
   cd chatbot
   python app.py
   # 또는
   python app.py --mode chat
   ```

2. **단일 쿼리 테스트**
   ```bash
   python app.py --mode test --query "지금 몇 시야?"
   ```

3. **벤치마크 테스트**
   ```bash
   python app.py --mode benchmark --iterations 3
   ```

4. **디버그 모드**
   ```bash
   python app.py --debug
   ```

### RAG 문서 처리 시스템 사용법

1. **문서 인덱싱**
   ```bash
   cd rag_ingest
   python run.py
   ```

2. **특정 문서 처리**
   ```bash
   python pipeline.py --input data/your_document.pdf
   ```

## 💬 사용 예시

```
🧑 사용자: 안녕하세요
🤖 AI: 안녕하세요! 무엇을 도와드릴까요?

🧑 사용자: 지금 몇 시야?
🤖 AI: 현재 시간은 2024년 12월 01일 14시 30분 25초입니다.

🧑 사용자: AAPL 주가 알려줘
🤖 AI: AAPL: $189.37

🧑 사용자: 명함을 제작하는 담당자는 누구야?
🤖 AI: 명함 제작을 담당하는 사람은 경영지원팀의 김봉석 대리입니다. 그는 근로계약, 연봉계약, 인사발령, 명함 제작, 사원증 관리, 휴가 관리, 세콤 관리, 임대차 관리 등의 업무를 맡고 있습니다. (출처: 제공된 컨텍스트)

🧑 사용자: 룰 DB 접속 설정 방법을 알려줘
🤖 AI: InnoRules 시스템에서 룰 DB 접속 설정을 하는 방법은 다음과 같습니다:

1. **룰 시스템 선택**: 먼저 룰 시스템을 선택합니다.

2. **룰 애플리케이션 설정**: 룰 애플리케이션 설정으로 이동합니다.

3. **룰 서비스의 유형 선택**: 로컬 룰 서비스 또는 원격 룰 서비스를 선택합니다.
   - **로컬 룰 서비스**를 선택하면 애플리케이션의 JVM 내에서 룰 서버가 실행되도록 구성됩니다.
   - **원격 룰 서비스**를 선택하면 TCP 커넥터 서버에 대한 정보를 입력해야 합니다.

4. **룰 DB 접속 설정**: 룰 DB에 접속하기 위한 정보를 입력합니다.
   - **데이터 소스 참조 방식**: 미리 만들어진 데이터 소스로부터 룰 DB 연결을 가져옵니다.
   - **전용 커넥션 풀 방식**: 로컬 룰 서버가 전용으로 사용할 커넥션 풀 데이터 소스를 로컬 생성합니다.

5. **필수 정보 입력**: 룰 DB에 접속하기 위해 다음 정보를 입력합니다.
   - 주소 (address)
   - 포트 (port, 기본값: 1521)
   - SID 또는 서비스 이름 (기본값: ORCL)
   - 사용자 계정
   - 비밀번호

이 정보를 입력하여 룰 DB를 등록하면 룰 서버가 룰 데이터를 조회할 수 있게 됩니다.

이 설정은 InnoRules Installation and Operation Guide v8에 기반한 것입니다. 추가적인 도움이 필요하시면 언제든지 문의하세요!

🧑 사용자: IRE-10041 에러에 대해 설명해봐
🤖 AI: IRE-10041 에러는 "데이터 룰 쿼리의 결과를 룰 시스템으로 변환할 수 없습니다."라는 메시지를 나타냅니다. 이 에러는 데이터 룰 쿼리를 실행한 후 그 결과의 각 컬럼 값을 대응하는 룰 리턴의 데이터 형식으로 변환하려고 했으나 변환이 지원되지 않을 때 발생합니다.

### 원인
- 데이터 룰 쿼리 결과의 컬럼 값이 룰 시스템에서 기대하는 데이터 형식으로 변환되지 않을 때 발생합니다.

### 조치 방법
- 이 에러가 발생하면 우선적으로 DBA(Database Administrator)에게 문의하여 문제를 해결하는 것이 좋습니다.

이 에러는 데이터베이스와 룰 시스템 간의 데이터 형식 불일치로 인해 발생할 수 있으므로, 데이터 형식을 확인하고 필요한 경우 변환 로직을 수정해야 할 수 있습니다.

🧑 사용자: quit
👋 대화를 종료합니다. 감사합니다!
📝 세션 로그 저장 완료: logs/chatbot_session_20241201_143025.txt
```

## 🛠️ 사용 가능한 도구

- **시간 조회**: 현재 시간 및 날짜 정보
- **주식 가격**: 실시간 주식 가격 조회 (yfinance 사용)
- **날씨 정보**: 특정 지역의 날씨 정보 (Mock 데이터)

## 🛠️ RAG에 등록된 문서(8개)

- **InnoRules Installation and Operation Guide.pdf**
- **InnoRules v8.0.5.0 Release Note.pdf** 
- **InnoRules_v8.0_InnoProduct_v8.0 WhitePaperv1.0.pdf**
- **경영지원실 업무 당당자 안내.txt**
- **본사 사무용품 구매 프로세스 안내.txt** 
- **연차휴가 사용 및 연차수당 지급방법.txt** 
- **자가운전, 육아수당 비과세 혜택 안내.txt**
- **회사 파일서버 권한 신청 절차 및 접근 방법.txt**

## 📁 프로젝트 구조

```
langgraph/
├── chatbot/              # 챗봇 시스템
│   ├── app.py           # 메인 애플리케이션
│   ├── config.py        # 설정 파일
│   ├── states.py        # 상태 정의
│   ├── prompts.py       # 시스템 프롬프트
│   ├── routers.py       # 라우팅 로직
│   ├── embeddings.py    # 임베딩 처리
│   ├── nodes/           # 워크플로우 노드들
│   │   ├── validate_input.py
│   │   ├── check_simple.py
│   │   ├── direct_answer.py
│   │   ├── generate.py
│   │   └── ...
│   ├── tools/           # 도구들
│   │   ├── time_tools.py
│   │   ├── finance_tools.py
│   │   └── weather_tools.py
│   ├── utils/           # 유틸리티
│   │   ├── logger.py
│   │   ├── llm_clients.py
│   │   └── ...
│   └── logs/            # 세션별 로그 파일
│       ├── chatbot_session_20241201_143025.txt
│       └── ...
└── rag_ingest/          # RAG 문서 처리 시스템
    ├── run.py           # 메인 실행 파일
    ├── pipeline.py      # 문서 처리 파이프라인
    ├── config.py        # 설정 파일
    ├── embeddings.py    # 임베딩 처리
    ├── chunkers.py      # 문서 청킹
    ├── store_chroma.py  # ChromaDB 저장
    ├── loaders/         # 문서 로더들
    ├── data/            # 처리할 문서들
    └── utils.py         # 유틸리티
```

## 🔧 워크플로우

### 챗봇 시스템 워크플로우
```
입력 검증 → 단순 질문 판별 → [직접 답변 | 검색 → 재순위 → 답변 생성]
                ↓
            도구 호출 → 결과 반영 → 최종 답변
```

### RAG 문서 처리 워크플로우
```
문서 로드 → 문서 청킹 → 임베딩 생성 → ChromaDB 저장 → 인덱싱 완료
```

## 📊 로그 시스템

- **세션별 로그**: 각 실행마다 별도의 로그 파일 생성
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR 모든 레벨 기록
- **로그 위치**: `logs/chatbot_session_YYYYMMDD_HHMMSS.txt`

## ⚠️ 주의사항

- OpenAI API Key가 필요합니다 (챗봇 시스템용)
- ChromaDB가 필요합니다 (RAG 시스템용)
- 주식 데이터는 yfinance를 통해 실시간 조회됩니다
- 날씨 정보는 현재 Mock 데이터를 사용합니다
- Tool 호출은 최대 3회로 제한됩니다

## 🚧 개발 예정

### 챗봇 시스템
- [v] RAG 시스템 구현 (벡터 검색)
- [ ] 더 많은 도구 추가
- [ ] 웹 인터페이스
- [ ] 성능 최적화

### RAG 문서 처리 시스템
- [v] 기본 문서 처리 파이프라인
- [ ] 더 많은 문서 형식 지원
- [v] 문서 업데이트 감지 및 재인덱싱
- [ ] 성능 최적화

## 📝 라이선스

MIT License

Copyright (c) 2025 Eungyu Lee. All rights reserved.

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🤝 기여

이슈나 풀 리퀘스트를 환영합니다!
