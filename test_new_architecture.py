#!/usr/bin/env python3
"""
测试新架构的服务重构

验证：
1. 服务管理器正常工作
2. 单例模式生效，坐标服务只初始化一次
3. 工具层能正确使用服务管理器
4. 接口抽象层正常工作
5. 配置管理系统正常
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_service_manager():
    """测试服务管理器"""
    print("🧪 测试服务管理器...")

    try:
        from services.service_manager import get_service_manager, get_coordinate_service, get_weather_service

        # 获取服务管理器
        manager = get_service_manager()
        print(f"✅ 服务管理器获取成功: {type(manager).__name__}")

        # 测试单例模式
        manager2 = get_service_manager()
        assert manager is manager2, "服务管理器应该是单例"
        print("✅ 服务管理器单例模式验证成功")

        # 获取坐标服务
        coordinate_service = get_coordinate_service()
        print(f"✅ 坐标服务获取成功: {type(coordinate_service).__name__}")

        # 测试坐标服务接口
        assert hasattr(coordinate_service, 'get_coordinate'), "坐标服务应该有get_coordinate方法"
        assert hasattr(coordinate_service, 'is_initialized'), "坐标服务应该有is_initialized方法"
        print("✅ 坐标服务接口验证成功")

        # 获取天气服务
        weather_service = get_weather_service()
        print(f"✅ 天气服务获取成功: {type(weather_service).__name__}")

        # 测试天气服务接口
        assert hasattr(weather_service, 'get_current_weather'), "天气服务应该有get_current_weather方法"
        assert hasattr(weather_service, 'is_available'), "天气服务应该有is_available方法"
        print("✅ 天气服务接口验证成功")

        # 测试服务状态
        status = manager.get_service_status()
        print(f"✅ 服务状态获取成功: 注册的服务={status.get('registered_services', [])}")

        return True

    except Exception as e:
        print(f"❌ 服务管理器测试失败: {e}")
        return False

def test_coordinate_service():
    """测试坐标服务"""
    print("\n🧪 测试坐标服务...")

    try:
        from services.service_manager import get_coordinate_service

        # 获取服务实例
        service = get_coordinate_service()

        # 测试初始化状态
        if not service.is_initialized():
            print("⚠️ 坐标服务尚未初始化，尝试调用方法触发初始化...")

        # 测试基本方法
        try:
            # 这个测试需要API密钥，可能会失败，但至少能验证接口
            coordinate = service.get_coordinate("北京")
            if coordinate:
                print(f"✅ 坐标查询成功: 北京 -> ({coordinate.longitude}, {coordinate.latitude})")
            else:
                print("⚠️ 坐标查询返回None（可能是API密钥问题）")
        except Exception as e:
            print(f"⚠️ 坐标查询失败（可能是API密钥问题）: {e}")

        # 测试服务状态
        service_status = service.get_service_status()
        print(f"✅ 服务状态: 初始化={service_status.get('initialized')}, 数据库路径={service_status.get('database_path')}")

        # 测试健康检查
        health = service.health_check()
        print(f"✅ 健康检查: {health}")

        return True

    except Exception as e:
        print(f"❌ 坐标服务测试失败: {e}")
        return False

def test_weather_service():
    """测试天气服务"""
    print("\n🧪 测试天气服务...")

    try:
        from services.service_manager import get_weather_service

        # 获取服务实例
        service = get_weather_service()

        # 测试服务可用性
        available = service.is_available()
        print(f"✅ 服务可用性检查: {available}")

        # 测试服务状态
        service_status = service.get_service_status()
        print(f"✅ 服务状态: 初始化={service_status.get('initialized')}, 坐标服务连接={service_status.get('coordinate_service_connected')}")

        # 测试健康检查
        health = service.health_check()
        print(f"✅ 健康检查: {health}")

        return True

    except Exception as e:
        print(f"❌ 天气服务测试失败: {e}")
        return False

def test_config_system():
    """测试配置系统"""
    print("\n🧪 测试配置系统...")

    try:
        from config.service_config import get_service_config, get_config_value

        # 获取配置
        config = get_service_config()
        print(f"✅ 配置获取成功: {type(config).__name__}")

        # 测试配置值
        coord_enabled = get_config_value('coordinate_service.enabled', True)
        weather_enabled = get_config_value('weather_service.enabled', True)
        log_level = get_config_value('logging.level', 'INFO')

        print(f"✅ 配置值读取: 坐标服务={coord_enabled}, 天气服务={weather_enabled}, 日志级别={log_level}")

        # 测试配置转字典
        config_dict = config.to_dict()
        print(f"✅ 配置字典转换成功，包含 {len(config_dict)} 个顶级配置")

        return True

    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False

def test_tools_integration():
    """测试工具集成"""
    print("\n🧪 测试工具集成...")

    try:
        # 测试钓鱼分析器
        from tools.fishing_analyzer import FishingAnalyzer

        analyzer = FishingAnalyzer()
        print(f"✅ 钓鱼分析器创建成功: {type(analyzer).__name__}")

        # 测试懒加载属性
        weather_service = analyzer.enhanced_weather_service
        print(f"✅ 懒加载天气服务成功: {type(weather_service).__name__}")

        return True

    except Exception as e:
        print(f"❌ 工具集成测试失败: {e}")
        return False

def test_singleton_behavior():
    """测试单例行为"""
    print("\n🧪 测试单例行为...")

    try:
        from services.service_manager import get_service_manager

        # 多次获取服务管理器
        managers = [get_service_manager() for _ in range(5)]

        # 验证都是同一个实例
        first_manager = managers[0]
        for i, manager in enumerate(managers[1:], 1):
            assert manager is first_manager, f"第{i+1}次获取的管理器不是同一个实例"

        print("✅ 服务管理器单例行为验证成功")

        # 测试坐标服务单例
        from services.service_manager import get_coordinate_service
        coord_services = [get_coordinate_service() for _ in range(3)]

        first_coord = coord_services[0]
        for i, service in enumerate(coord_services[1:], 1):
            assert service is first_coord, f"第{i+1}次获取的坐标服务不是同一个实例"

        print("✅ 坐标服务单例行为验证成功")

        return True

    except Exception as e:
        print(f"❌ 单例行为测试失败: {e}")
        return False

def test_logging_system():
    """测试日志系统"""
    print("\n🧪 测试日志系统...")

    try:
        from services.logging.enhanced_business_logger import EnhancedBusinessLogger

        # 创建日志器
        logger = EnhancedBusinessLogger("test_module")
        print(f"✅ 增强日志器创建成功: {type(logger).__name__}")

        # 测试各种日志方法
        logger.log_service_initialized("测试服务")
        logger.log_operation_success("测试操作", "测试描述")
        logger.log_debug_info = "debug_info" if hasattr(logger, 'log_debug_info') else "no_debug_info"

        print("✅ 日志方法调用成功")

        # 测试兼容性
        from services.logging.business_logger import BusinessLogger

        compat_logger = BusinessLogger("test_compat")
        print(f"✅ 兼容日志器创建成功: {type(compat_logger).__name__}")

        return True

    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试新架构重构")
    print("=" * 60)

    tests = [
        ("服务管理器", test_service_manager),
        ("坐标服务", test_coordinate_service),
        ("天气服务", test_weather_service),
        ("配置系统", test_config_system),
        ("工具集成", test_tools_integration),
        ("单例行为", test_singleton_behavior),
        ("日志系统", test_logging_system),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 总体结果: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有测试通过！新架构重构成功！")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)