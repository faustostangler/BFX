from beatforge.config import FILENAME


def load_playlists(file_path: str = FILENAME + ".txt") -> dict[str, list[str]]:
    """
    Lê um arquivo de texto contendo blocos:
      <GÊNERO>
      <URL1>
      <URL2>
      ...
      <GÊNERO>
      ...
    e retorna um dict mapeando cada gênero à sua lista de URLs.
    """
    playlists: dict[str, list[str]] = {}
    current_genre: str | None = None

    try:
        with open(file_path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                # Se não começa com "http", é uma nova categoria (gênero)
                if not line.lower().startswith("http"):
                    current_genre = line
                    playlists[current_genre] = []
                else:
                    if current_genre is None:
                        raise ValueError(f"URL sem gênero associado: {line}")
                    playlists[current_genre].append(line)
    except Exception as e:
        return {}

    return playlists
