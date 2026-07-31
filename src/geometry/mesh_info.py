import pyvista as pv


def format_mesh_info(mesh: pv.DataSet) -> str:
    """Retorna informações básicas da malha em formato de texto."""

    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds

    size_x = xmax - xmin
    size_y = ymax - ymin
    size_z = zmax - zmin

    return (
        f"Pontos: {mesh.n_points:,}\n"
        f"Células: {mesh.n_cells:,}\n"
        f"Dimensões X: {size_x:.2f} mm\n"
        f"Dimensões Y: {size_y:.2f} mm\n"
        f"Dimensões Z: {size_z:.2f} mm"
    )