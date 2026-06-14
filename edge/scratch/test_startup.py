try:
    from main import app
    print(f"App loaded successfully. Route count: {len(app.routes)}")
except Exception as e:
    import traceback
    traceback.print_exc()
