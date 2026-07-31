from pathlib import Path

import pyvista as pv


def load_stl(file_path: str) -> pv.DataSet:
    """Carrega uma malha STL e verifica se o arquivo é válido."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() != ".stl":
        raise ValueError("O arquivo selecionado não é um STL.")

    mesh = pv.read(path)

    if mesh.n_points == 0 or mesh.n_cells == 0:
        raise ValueError("A malha STL está vazia ou é inválida.")

    return mesh