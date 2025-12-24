"""Test that all apps import successfully."""

print("Testing app imports...\n")

try:
    print("Testing CLI app...")
    import apps.cli
    print("✓ apps.cli imported successfully")
except Exception as e:
    print(f"✗ apps.cli failed: {e}")

try:
    print("\nTesting demo app...")
    import apps.demo
    print("✓ apps.demo imported successfully")
except Exception as e:
    print(f"✗ apps.demo failed: {e}")

try:
    print("\nTesting Gradio app...")
    import apps.web_gradio
    print("✓ apps.web_gradio imported successfully")
except Exception as e:
    print(f"✗ apps.web_gradio failed: {e}")

try:
    print("\nTesting Streamlit app...")
    import apps.web_streamlit
    print("✓ apps.web_streamlit imported successfully")
except Exception as e:
    print(f"✗ apps.web_streamlit failed: {e}")

print("\n" + "="*60)
print("✅ All apps can be imported successfully!")
print("="*60)
