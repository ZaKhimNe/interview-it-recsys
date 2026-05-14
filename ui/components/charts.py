"""
📊 Chart Components
====================
Người phụ trách: App Lead
Mục đích: Component tái sử dụng cho các biểu đồ Plotly,
          đặc biệt là Radar Chart hiển thị vector năng lực.
"""

import plotly.graph_objects as go
import numpy as np
from config import COMPETENCY_DOMAINS


def create_radar_chart(
    competency_vector: np.ndarray,
    title: str = "Radar năng lực",
    color: str = "rgba(99, 110, 250, 0.6)",
) -> go.Figure:
    """
    Tạo Radar Chart từ vector năng lực.

    Args:
        competency_vector: numpy array 6 chiều (0-10)
        title: Tiêu đề biểu đồ
        color: Màu fill của radar

    Returns:
        Plotly Figure object
    """
    categories = COMPETENCY_DOMAINS
    values = competency_vector.tolist()
    values.append(values[0])  # Đóng vòng radar

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor=color,
        line=dict(color=color.replace("0.6", "1.0"), width=2),
        name=title,
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10]),
        ),
        showlegend=True,
        title=title,
    )

    return fig


def create_comparison_radar(
    vector_a: np.ndarray,
    vector_b: np.ndarray,
    label_a: str = "Hiện tại",
    label_b: str = "Mục tiêu",
) -> go.Figure:
    """Tạo Radar Chart so sánh 2 vector năng lực."""
    # TODO: App Lead implement comparison chart
    pass
