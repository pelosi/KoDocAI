from typing import Optional
import time

class Logger:
    def __init__(self) -> None:
        self.overall_start: float = time.time()  # 전체 시작 시간
        self.current_step: Optional[str] = None  # 현재 단계 이름
        self.step_start_time: Optional[float] = None  # 현재 단계 시작 시간

    def start(self, step_name: str) -> None:
        """단계 시작 로그를 출력"""
        self.current_step = step_name
        self.step_start_time = time.time()
        print(f"[{self.step_start_time - self.overall_start:.2f}초] {step_name} 시작")

    def end(self) -> None:
        """단계 종료 로그를 출력"""
        if self.current_step is None or self.step_start_time is None:
            raise ValueError("종료할 단계가 시작되지 않았습니다.")
        end_time: float = time.time()
        duration: float = end_time - self.step_start_time
        elapsed: float = end_time - self.overall_start
        print(f"[{elapsed:.2f}초] {self.current_step} 완료 (소요 시간: {duration:.2f}초)")
        self.current_step = None
        self.step_start_time = None
