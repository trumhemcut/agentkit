"""
Manual test script to verify OTP component generation

Run this to see the generated OTP component structure.
"""

import json
from tools.a2ui_tools import OTPInputTool


def test_basic_otp():
    """Test basic 6-digit OTP generation"""
    print("=" * 60)
    print("TEST: Basic 6-digit OTP")
    print("=" * 60)
    
    tool = OTPInputTool()
    result = tool.generate_component(
        title="Verify your email",
        description="Enter the 6-digit code sent to your email.",
        max_length=6
    )
    
    print("\n📦 Component ID:", result["component_id"])
    print("\n🔧 Component Structure:")
    print(json.dumps(result["component"].model_dump(), indent=2))
    print("\n📊 Data Model:")
    print(json.dumps({
        "path": result["data_model"]["path"],
        "contents": [c.model_dump() for c in result["data_model"]["contents"]]
    }, indent=2))


def test_otp_with_separator():
    """Test OTP with separator (123-456)"""
    print("\n" + "=" * 60)
    print("TEST: 6-digit OTP with separator at position 3")
    print("=" * 60)
    
    tool = OTPInputTool()
    result = tool.generate_component(
        title="Two-Factor Authentication",
        description="Enter the code from your authenticator app",
        max_length=6,
        separator_positions=[3]
    )
    
    print("\n📦 Component ID:", result["component_id"])
    print("\n🔧 Component Structure:")
    component_dict = result["component"].model_dump()
    otp_props = component_dict["component"]["OTPInput"]
    print(f"  Title: {otp_props['title']['literalString']}")
    print(f"  Max Length: {otp_props['maxLength']}")
    print(f"  Groups: {otp_props['groups']}")
    print(f"  Pattern Type: {otp_props['patternType']}")


def test_phone_verification():
    """Test 4-digit phone verification OTP"""
    print("\n" + "=" * 60)
    print("TEST: 4-digit phone verification OTP (12-34)")
    print("=" * 60)
    
    tool = OTPInputTool()
    result = tool.generate_component(
        title="Verify your phone",
        description="Enter the 4-digit code sent via SMS",
        max_length=4,
        separator_positions=[2],
        button_text="Verify Phone"
    )
    
    print("\n📦 Component ID:", result["component_id"])
    component_dict = result["component"].model_dump()
    otp_props = component_dict["component"]["OTPInput"]
    print(f"  Title: {otp_props['title']['literalString']}")
    print(f"  Max Length: {otp_props['maxLength']}")
    print(f"  Groups: {otp_props['groups']}")
    print(f"  Button Text: {otp_props['buttonText']['literalString']}")


def test_alphanumeric_otp():
    """Test alphanumeric OTP"""
    print("\n" + "=" * 60)
    print("TEST: Alphanumeric OTP")
    print("=" * 60)
    
    tool = OTPInputTool()
    result = tool.generate_component(
        title="Enter recovery code",
        description="Enter your 6-character recovery code",
        max_length=6,
        pattern_type="alphanumeric"
    )
    
    print("\n📦 Component ID:", result["component_id"])
    component_dict = result["component"].model_dump()
    otp_props = component_dict["component"]["OTPInput"]
    print(f"  Pattern Type: {otp_props['patternType']}")
    print(f"  Groups: {otp_props['groups']}")


if __name__ == "__main__":
    print("\n🧪 OTP Component Generation Tests\n")
    
    test_basic_otp()
    test_otp_with_separator()
    test_phone_verification()
    test_alphanumeric_otp()
    
    print("\n" + "=" * 60)
    print("✅ All manual tests completed successfully!")
    print("=" * 60 + "\n")
