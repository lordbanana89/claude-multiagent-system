#!/usr/bin/env python3
"""
Simple test per verificare i componenti enhanced messaging uno per volta
"""

def test_notifications():
    """Test solo le notifiche"""
    print("🔔 Testing Notifications...")
    try:
        # Test import
        from messaging.notifications import AgentNotificationSystem, NotificationConfig
        print("✅ Import successful")

        # Test initialization
        notif_system = AgentNotificationSystem()
        print("✅ System initialized")

        # Test agent registration
        config = NotificationConfig(
            agent_id="test-agent",
            enable_audio=False,
            enable_visual=False
        )
        notif_system.register_agent("test-agent", config)
        print("✅ Agent registered")

        # Shutdown
        notif_system.shutdown()
        print("✅ Notifications test passed")
        return True

    except Exception as e:
        print(f"❌ Notifications test failed: {e}")
        return False

def test_classification():
    """Test solo la classificazione"""
    print("\n🏷️ Testing Classification...")
    try:
        from messaging.classification import MessageClassifier, MessageType
        print("✅ Import successful")

        classifier = MessageClassifier()
        print("✅ Classifier initialized")

        # Test basic functionality
        stats = classifier.get_classification_stats()
        print(f"✅ Stats working: {stats}")

        print("✅ Classification test passed")
        return True

    except Exception as e:
        print(f"❌ Classification test failed: {e}")
        return False

def test_workflow():
    """Test solo il workflow"""
    print("\n🔄 Testing Workflow...")
    try:
        from messaging.workflow import AgentDecisionEngine, AgentConfig, AgentCapability
        print("✅ Import successful")

        engine = AgentDecisionEngine()
        print("✅ Engine initialized")

        # Test basic functionality
        stats = engine.get_workflow_stats()
        print(f"✅ Stats working: {stats}")

        engine.shutdown()
        print("✅ Workflow test passed")
        return True

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def test_interface():
    """Test solo l'interface"""
    print("\n💻 Testing Interface...")
    try:
        from messaging.interface import EnhancedTerminalInterface
        print("✅ Import successful")

        interface = EnhancedTerminalInterface()
        print("✅ Interface initialized")

        # Test command creation
        inbox_cmd = interface.create_inbox_command("test-agent")
        print("✅ Inbox command created")

        # Test help command
        help_result = inbox_cmd("help")
        print(f"✅ Help command working: {len(help_result)} chars")

        print("✅ Interface test passed")
        return True

    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        return False

def test_management():
    """Test solo il management"""
    print("\n📊 Testing Management...")
    try:
        from messaging.management import MessageLifecycleManager, IntelligentInbox
        print("✅ Import successful")

        manager = MessageLifecycleManager()
        print("✅ Manager initialized")

        # Test basic functionality
        inbox = manager.get_inbox("test-agent")
        print(f"✅ Inbox created: {type(inbox)}")

        stats = manager.get_system_statistics()
        print(f"✅ System stats working: {stats}")

        manager.shutdown()
        print("✅ Management test passed")
        return True

    except Exception as e:
        print(f"❌ Management test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SIMPLE ENHANCED MESSAGING TESTS")
    print("=" * 50)

    results = []
    results.append(("Notifications", test_notifications()))
    results.append(("Classification", test_classification()))
    results.append(("Workflow", test_workflow()))
    results.append(("Interface", test_interface()))
    results.append(("Management", test_management()))

    print("\n" + "=" * 50)
    print("📊 RESULTS:")

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1

    success_rate = passed / len(results) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}% ({passed}/{len(results)})")

    if success_rate == 100:
        print("🎉 ALL BASIC TESTS PASSED!")
    else:
        print("⚠️ Some components need fixing")