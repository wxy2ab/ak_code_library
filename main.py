from core.run_content import run_content

if __name__ =="__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python run_content.py <n>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    run_content(n)