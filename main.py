from agent import create_chat_session


def main():
    print("🤖 Iniciando Agente EDA...")
    try:
        chat = create_chat_session()
        print("✅ Agente EDA con Gemini (SDK Unificado + Flash Lite) listo.")
        print("Escribe 'salir' para terminar.\n")
    except Exception as e:
        print(f"❌ Error al inicializar el agente: {e}")
        return

    while True:
        try:
            user_input = input("Tú: ")
        except (KeyboardInterrupt, EOFError):
            print("\nAgente: ¡Hasta pronto!")
            break

        if user_input.lower() in ["salir", "exit", "quit", "q"]:
            print("Agente: ¡Hasta pronto!")
            break

        try:
            response = chat.send_message(user_input)
            print("\nAgente:", response.text, "\n")
        except Exception as e:
            print(f"\n[Error de comunicación con la API]: {e}\n")


if __name__ == "__main__":
    main()
