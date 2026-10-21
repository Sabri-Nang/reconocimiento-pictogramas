"""Persistencia y gráficos comunes de entrenamiento."""
from __future__ import annotations

from .artifacts import save_figure


def plot_history(rows, dest, title, phase_boundary=None, train_images=1200):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not rows:
        return
    epochs = [row["epoch"] for row in rows]
    best = min(rows, key=lambda row: row["val_loss"])["epoch"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    for key, label in [("loss", "Entrenamiento (aumentos activos)"), ("val_loss", "Validación interna")]:
        axes[0].plot(epochs, [row[key] for row in rows], label=label)
    axes[0].set(ylabel="Entropía cruzada", title="Pérdida: criterio de parada")
    for key, label in [("accuracy", "Entrenamiento (durante los ajustes)"), ("val_accuracy", "Validación interna")]:
        axes[1].plot(epochs, [row[key] * 100 for row in rows], label=label)
    axes[1].set(ylabel="Exactitud (%)", title="Porcentaje de aciertos", ylim=(0, 101))
    axes[2].plot(epochs, [row["val_correct"] for row in rows], label="Aciertos de validación")
    axes[2].plot(epochs, [row["val_errors"] for row in rows], label="Errores de validación")
    axes[2].set(ylabel="Imágenes de 300", title="Aciertos y errores: validación interna", ylim=(0, 305))
    for axis in axes:
        axis.set_xlabel(f"Época global (una vuelta a las {train_images} imágenes)")
        axis.axvline(best, color="black", linestyle="--", linewidth=1, label=f"Menor pérdida: época {best}")
        axis.axvline(epochs[-1], color="gray", linestyle="-.", linewidth=1, label=f"Última ejecutada: época {epochs[-1]}")
        if phase_boundary:
            axis.axvline(phase_boundary + 0.5, color="gray", linestyle=":", label="Comienza ajuste fino")
        axis.legend(fontsize=7)
        axis.grid(alpha=0.15)
    fig.suptitle(title)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.text(0.02, 0.02, "Fuente: historial de esta ronda. La sesión externa no se consulta por época.", fontsize=8)
    save_figure(fig, dest / "epoch_curves.png", dpi=140)
    plt.close(fig)
