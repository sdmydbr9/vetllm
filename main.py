from scripts.ui import create_ui

def main():
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
