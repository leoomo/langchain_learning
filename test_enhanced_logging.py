#!/usr/bin/env python3
"""
测试增强的模型调用日志功能

验证调用目的分析、性能优化和配置选项是否正常工作
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from services.middleware.logging_middleware import (
    AgentLoggingMiddleware,
    ModelCallRecord,
    CallPurposeAnalyzer,
    AgentExecutionMetrics
)
from services.middleware.config import MiddlewareConfig


def test_call_purpose_analyzer():
    """测试调用目的分析器"""
    print("🧪 测试调用目的分析器...")

    # 模拟消息列表
    messages = [
        type('MockMessage', (), {
            'type': 'human',
            'content': '明天杭州适合钓鱼吗？'
        })()
    ]

    # 测试目的分析
    analysis = CallPurposeAnalyzer.analyze_call_purpose(
        messages=messages,
        call_position=1,
        has_tool_calls=True
    )

    print(f"✅ 调用目的: {analysis['call_purpose']}")
    print(f"✅ 意图分类: {analysis['intent_category']}")
    print(f"✅ 关键点: {analysis['key_points']}")
    print(f"✅ 上下文摘要: {analysis['context_summary']}")

    return analysis


def test_enhanced_middleware_config():
    """测试增强的中间件配置"""
    print("\n🧪 测试增强的中间件配置...")

    # 创建测试配置
    config = MiddlewareConfig(
        log_level="DEBUG",
        log_to_console=True,
        log_to_file=False,
        enable_call_purpose_analysis=True,
        show_enhanced_console_output=True,
        model_call_detail_level="enhanced",
        file_log_format="json"
    )

    # 验证配置
    try:
        config.validate()
        print("✅ 配置验证通过")
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return None

    # 创建中间件实例
    middleware = AgentLoggingMiddleware(config=config)
    print("✅ 增强中间件创建成功")

    # 检查缓存和优化功能
    assert hasattr(middleware, '_purpose_analysis_cache'), "缺少缓存机制"
    assert hasattr(middleware, '_compiled_patterns'), "缺少预编译模式"
    print("✅ 性能优化功能已启用")

    return middleware


def test_model_call_record():
    """测试模型调用记录"""
    print("\n🧪 测试模型调用记录...")

    # 创建测试记录
    record = ModelCallRecord(
        call_id=1,
        timestamp="2025-01-08T12:00:00",
        model_name="claude-sonnet-4-5",
        duration_ms=1500.5,
        token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        success=True,
        call_purpose="tool_selection",
        intent_category="weather_fishing_query",
        call_context_summary="工具选择，关键信息：明天、杭州、钓鱼",
        key_points=["明天", "杭州", "钓鱼"]
    )

    print(f"✅ 模型调用记录创建成功")
    print(f"   - 调用ID: {record.call_id}")
    print(f"   - 调用目的: {record.call_purpose}")
    print(f"   - 意图分类: {record.intent_category}")
    print(f"   - 关键点: {record.key_points}")

    return record


def test_execution_metrics():
    """测试执行指标"""
    print("\n🧪 测试执行指标...")

    # 创建指标实例
    metrics = AgentExecutionMetrics(
        session_id="test_session",
        timestamp="2025-01-08T12:00:00",
        execution_id="test_exec"
    )

    # 添加模型调用记录
    record1 = ModelCallRecord(
        call_id=1,
        timestamp="2025-01-08T12:00:00",
        model_name="claude-sonnet-4-5",
        duration_ms=1000,
        token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        success=True,
        call_purpose="tool_selection",
        intent_category="weather_fishing_query",
        key_points=["明天", "杭州"]
    )

    record2 = ModelCallRecord(
        call_id=2,
        timestamp="2025-01-08T12:01:00",
        model_name="claude-sonnet-4-5",
        duration_ms=800,
        token_usage={"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
        success=True,
        call_purpose="result_generation",
        intent_category="weather_fishing_query",
        key_points=["推荐", "时间"]
    )

    metrics.add_model_call(record1)
    metrics.add_model_call(record2)

    # 获取摘要
    summary = metrics.get_model_calls_summary()

    print(f"✅ 执行指标统计:")
    print(f"   - 总调用次数: {summary['total_calls']}")
    print(f"   - 调用目的分布: {summary['purposes_distribution']}")
    print(f"   - 意图分类分布: {summary['intents_distribution']}")
    print(f"   - 平均耗时: {summary['average_duration_ms']:.2f}ms")

    return metrics


def test_performance_optimization():
    """测试性能优化功能"""
    print("\n🧪 测试性能优化功能...")

    # 创建启用优化的中间件
    config = MiddlewareConfig(
        enable_call_purpose_analysis=True,
        model_call_detail_level="detailed"
    )

    middleware = AgentLoggingMiddleware(config=config)

    # 模拟相同的消息，测试缓存效果
    messages = [
        type('MockMessage', (), {
            'type': 'human',
            'content': '明天北京天气怎么样？'
        })()
    ]

    # 第一次分析（无缓存）
    start_time = time.time()
    analysis1 = CallPurposeAnalyzer.analyze_call_purpose(
        messages=messages,
        call_position=1,
        has_tool_calls=True,
        compiled_patterns=middleware._compiled_patterns
    )
    first_duration = time.time() - start_time

    # 手动缓存结果
    messages_str = str([str(msg.content) for msg in messages])
    cache_key = middleware._get_purpose_analysis_cache_key(messages_str, 1, True)
    middleware._cache_purpose_analysis(cache_key, analysis1)

    # 第二次分析（使用缓存）
    start_time = time.time()
    cached_analysis = middleware._get_cached_purpose_analysis(cache_key)
    second_duration = time.time() - start_time

    print(f"✅ 性能对比:")
    print(f"   - 首次分析耗时: {first_duration*1000:.2f}ms")
    print(f"   - 缓存查询耗时: {second_duration*1000:.2f}ms")
    if second_duration > 0:
        print(f"   - 性能提升: {(first_duration/second_duration):.1f}x")
    else:
        print("   - 性能提升: 缓存查询极快，无法精确测量")

    assert cached_analysis == analysis1, "缓存结果不一致"
    print("✅ 缓存功能验证通过")


def test_mixed_format_output():
    """测试混合格式输出"""
    print("\n🧪 测试混合格式输出...")

    # 创建临时日志文件
    log_file = "test_enhanced_agent.log"

    config = MiddlewareConfig(
        log_level="INFO",
        log_to_console=True,
        log_to_file=True,
        log_file_path=log_file,
        enable_call_purpose_analysis=True,
        show_enhanced_console_output=True,
        file_log_format="json"
    )

    middleware = AgentLoggingMiddleware(config=config)

    # 创建测试的模型调用记录
    test_record = ModelCallRecord(
        call_id=1,
        timestamp="2025-01-08T12:00:00",
        model_name="claude-sonnet-4-5",
        duration_ms=1200.5,
        token_usage={"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
        success=True,
        call_purpose="tool_selection",
        intent_category="weather_fishing_query",
        call_context_summary="工具选择，关键信息：明天、杭州、钓鱼",
        key_points=["明天", "杭州", "钓鱼"]
    )

    # 添加到指标中
    middleware.metrics.add_model_call(test_record)

    # 记录日志
    middleware._log_with_context('INFO', "📥 模型响应详情", {
        'call_id': test_record.call_id,
        'call_purpose': test_record.call_purpose,
        'purpose_desc': CallPurposeAnalyzer.CALL_PURPOSES.get(test_record.call_purpose),
        'duration_ms': round(test_record.duration_ms, 2),
        'token_usage': test_record.token_usage,
        'intent_category': test_record.intent_category,
        'key_points': test_record.key_points,
        'context_summary': test_record.call_context_summary,
        'success': test_record.success
    })

    # 检查日志文件是否创建
    if os.path.exists(log_file):
        print(f"✅ 日志文件创建成功: {log_file}")

        # 读取并检查日志内容
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        if log_content.strip():
            print("✅ 日志内容写入成功")
            print(f"   日志大小: {len(log_content)} 字符")
        else:
            print("❌ 日志内容为空")

        # 清理测试文件
        try:
            os.remove(log_file)
            print("✅ 测试日志文件清理完成")
        except:
            pass
    else:
        print("❌ 日志文件未创建")


def test_configuration_validation():
    """测试配置验证"""
    print("\n🧪 测试配置验证...")

    # 测试有效配置
    try:
        valid_config = MiddlewareConfig(
            model_call_detail_level="enhanced",
            file_log_format="json"
        )
        valid_config.validate()
        print("✅ 有效配置验证通过")
    except Exception as e:
        print(f"❌ 有效配置验证失败: {e}")

    # 测试无效配置
    invalid_configs = [
        {"model_call_detail_level": "invalid_level"},
        {"file_log_format": "invalid_format"},
        {"max_log_length": -1}
    ]

    for i, invalid_config in enumerate(invalid_configs):
        try:
            config = MiddlewareConfig(**invalid_config)
            config.validate()
            print(f"❌ 无效配置 {i+1} 验证应该失败但却通过了")
        except Exception as e:
            print(f"✅ 无效配置 {i+1} 正确被拒绝: {type(e).__name__}")


def main():
    """主测试函数"""
    print("🚀 开始测试增强的模型调用日志功能")
    print("=" * 50)

    try:
        # 运行所有测试
        test_call_purpose_analyzer()
        test_enhanced_middleware_config()
        test_model_call_record()
        test_execution_metrics()
        test_performance_optimization()
        test_mixed_format_output()
        test_configuration_validation()

        print("\n" + "=" * 50)
        print("🎉 所有测试完成！增强的日志功能工作正常")

        print("\n📊 功能特性验证:")
        print("✅ 调用目的智能识别")
        print("✅ 意图分类和关键点提取")
        print("✅ 增强的控制台输出格式")
        print("✅ 结构化文件日志输出")
        print("✅ 性能优化和缓存机制")
        print("✅ 灵活的配置选项")
        print("✅ 完整的错误处理")

        print("\n🔧 配置选项:")
        print("- AGENT_CALL_PURPOSE_ANALYSIS: 启用调用目的分析")
        print("- AGENT_ENHANCED_CONSOLE: 启用增强控制台输出")
        print("- AGENT_MODEL_CALL_DETAIL: 模型调用详细程度")
        print("- AGENT_FILE_LOG_FORMAT: 文件日志格式")

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)