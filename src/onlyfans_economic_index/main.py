"""Module principal Hello World."""


def hello(name: str = "World") -> str:
    """Retourne un message de salutation.

    Args:
        name: Le nom à saluer (défaut: "World")

    Returns:
        Message de salutation formaté
    """
    return f"Hello, {name}!"


def main() -> None:
    """Point d'entrée principal."""
    print(hello())

    # Exemple interactif
    user_name = input("Quel est votre nom ? ")
    if user_name.strip():
        print(hello(user_name))


if __name__ == "__main__":
    main()
