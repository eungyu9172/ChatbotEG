import logging
import os
from pathlib import Path
from datetime import datetime
from config import LOGGING_CONFIG


class SessionLogger:
    """세션별 로그 파일 관리"""
    
    def __init__(self):
        self.log_dir = Path(LOGGING_CONFIG["log_directory"])
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = None
        self.log_filepath = None
        self.file_handler = None
        self.logger = None
        
    def start_session(self):
        """새 세션 시작 - 로그 파일 생성"""
        if not LOGGING_CONFIG.get("log_to_file", False):
            return
            
        # 세션 ID 생성 (타임스탬프 기반)
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"chatbot_session_{self.session_id}.txt"
        self.log_filepath = self.log_dir / log_filename
        
        # 파일 핸들러 생성
        self.file_handler = logging.FileHandler(self.log_filepath, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)  # DEBUG 레벨까지 기록
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        
        # 로거에 핸들러 추가
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(self.file_handler)
        
        # 세션 시작 로그
        self.logger.info(f"=== 챗봇 세션 시작 ===")
        self.logger.info(f"세션 ID: {self.session_id}")
        self.logger.info(f"로그 파일: {self.log_filepath}")
        
    def end_session(self):
        """세션 종료 - 로그 파일 완료"""
        if self.file_handler and self.logger:
            self.logger.info(f"=== 챗봇 세션 종료 ===")
            self.logger.info(f"세션 ID: {self.session_id}")
            self.logger.info(f"로그 파일 완료: {self.log_filepath}")
            
            # 핸들러 제거 및 파일 닫기
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()
            
            print(f"📝 세션 로그 저장 완료: {self.log_filepath}")


# 전역 세션 로거 인스턴스
session_logger = SessionLogger()


def setup_logger():
    """로거 설정"""
    level = getattr(logging, LOGGING_CONFIG["log_level"])
    
    # 로거 생성
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()
