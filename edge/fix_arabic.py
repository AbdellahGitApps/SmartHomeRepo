import io

def test_fix():
    with io.open("e:/SmartHomeMobileApp/edge/dashboard/templates/base.html", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    with io.open("e:/SmartHomeMobileApp/edge/test_arabic_out.txt", "w", encoding="utf-8") as out:
        for line in lines:
            if "nav_dashboard:" in line:
                out.write("Original: " + line.strip() + "\n")
                try:
                    # Reverse the cp1256 double-encoding
                    fixed = line.encode('cp1256').decode('utf-8')
                    out.write("Fixed: " + fixed.strip() + "\n")
                except Exception as e:
                    out.write("Error: " + str(e) + "\n")
                break

if __name__ == "__main__":
    test_fix()
