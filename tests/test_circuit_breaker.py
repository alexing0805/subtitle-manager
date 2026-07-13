"""
字幕源熔断器单元测试
"""
import os
import sys
import asyncio
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.subtitle_sources import (
    CircuitBreaker,
    CircuitBreakerOpen,
    get_circuit_breaker,
)


class TestCircuitBreaker:
    """CircuitBreaker 类的测试"""

    @pytest.mark.asyncio
    async def test_initial_state(self):
        """测试初始状态为 closed"""
        breaker = CircuitBreaker("test_source")
        assert breaker._state == "closed"
        assert breaker._failures == 0
        assert breaker.is_open is False
        assert breaker.is_half_open is False

    @pytest.mark.asyncio
    async def test_can_proceed_when_closed(self):
        """closed 状态下允许请求"""
        breaker = CircuitBreaker("test_source")
        assert await breaker.can_proceed() is True

    @pytest.mark.asyncio
    async def test_record_success_resets_failures(self):
        """记录成功会重置失败计数"""
        breaker = CircuitBreaker("test_source")
        breaker.record_failure()
        breaker.record_failure()
        assert breaker._failures == 2
        breaker.record_success()
        assert breaker._failures == 0
        assert breaker._state == "closed"

    @pytest.mark.asyncio
    async def test_record_failure_increments_count(self):
        """记录失败会增加计数"""
        breaker = CircuitBreaker("test_source")
        breaker.record_failure()
        assert breaker._failures == 1
        breaker.record_failure()
        assert breaker._failures == 2

    @pytest.mark.asyncio
    async def test_opens_after_max_failures(self):
        """达到最大失败次数后熔断器断开"""
        breaker = CircuitBreaker("test_source")
        for _ in range(CircuitBreaker.MAX_FAILURES):
            breaker.record_failure()
        assert breaker._state == "open"
        assert breaker.is_open is True

    @pytest.mark.asyncio
    async def test_cannot_proceed_when_open(self):
        """open 状态下不允许请求"""
        breaker = CircuitBreaker("test_source")
        for _ in range(CircuitBreaker.MAX_FAILURES):
            breaker.record_failure()
        # 直接设置为 open 状态后 can_proceed 应该返回 False
        breaker._state = "open"
        assert await breaker.can_proceed() is False

    @pytest.mark.asyncio
    async def test_half_open_after_wait(self):
        """等待时间过后进入半开状态"""
        import time
        breaker = CircuitBreaker("test_source")
        for _ in range(CircuitBreaker.MAX_FAILURES):
            breaker.record_failure()
        breaker._state = "open"
        breaker._last_failure_time = time.monotonic() - CircuitBreaker.HALF_OPEN_WAIT - 1
        assert await breaker.can_proceed() is True
        assert breaker._state == "half_open"


class TestCircuitBreakerContext:
    """circuit_breaker_context 上下文管理器的测试"""

    @pytest.mark.asyncio
    async def test_normal_execution(self):
        """正常执行应该成功"""
        from backend.subtitle_sources import circuit_breaker_context

        async with circuit_breaker_context("test_source") as breaker:
            assert breaker is not None
            assert breaker.record_success is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_raises(self):
        """熔断器断开时应该抛出异常"""
        from backend.subtitle_sources import circuit_breaker_context

        # 设置熔断器为 open 状态
        breaker = get_circuit_breaker("test_source_open")
        for _ in range(CircuitBreaker.MAX_FAILURES):
            breaker.record_failure()
        breaker._state = "open"

        with pytest.raises(CircuitBreakerOpen):
            async with circuit_breaker_context("test_source_open"):
                pass

    @pytest.mark.asyncio
    async def test_success_recorded(self):
        """成功时应该记录到熔断器"""
        from backend.subtitle_sources import circuit_breaker_context

        breaker = get_circuit_breaker("test_source_success")
        initial_failures = breaker._failures

        async with circuit_breaker_context("test_source_success"):
            pass

        assert breaker._failures == initial_failures  # 成功不会增加失败计数

    @pytest.mark.asyncio
    async def test_failure_recorded_on_exception(self):
        """异常时应该记录到熔断器"""
        from backend.subtitle_sources import circuit_breaker_context

        breaker = get_circuit_breaker("test_source_exception")
        initial_failures = breaker._failures

        with pytest.raises(ValueError):
            async with circuit_breaker_context("test_source_exception"):
                raise ValueError("Test error")

        # 失败计数应该增加
        assert breaker._failures > initial_failures


class TestGetCircuitBreaker:
    """get_circuit_breaker 函数的测试"""

    def test_returns_same_instance(self):
        """同一名称返回相同实例"""
        breaker1 = get_circuit_breaker("shared_source")
        breaker2 = get_circuit_breaker("shared_source")
        assert breaker1 is breaker2

    def test_different_instances_for_different_names(self):
        """不同名称返回不同实例"""
        breaker1 = get_circuit_breaker("source_a")
        breaker2 = get_circuit_breaker("source_b")
        assert breaker1 is not breaker2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
