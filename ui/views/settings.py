"""Matching settings view."""

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from ui import widgets


def render_settings(app) -> None:
    app.crumb.setText("Settings")
    outer = widgets.page(
        app,
        "Settings",
        "Configure matching behavior before scanning.",
    )

    algorithm = widgets.card()
    algorithm_layout = QVBoxLayout(algorithm)
    algorithm_layout.setContentsMargins(22, 20, 22, 20)
    heading = QLabel("Soft weighted token matching")
    heading.setObjectName("cardTitle")
    detail = QLabel(
        "Handles reordered words while reducing common-token influence."
    )
    detail.setObjectName("muted")
    algorithm_layout.addWidget(heading)
    algorithm_layout.addWidget(detail)
    outer.addWidget(algorithm)

    thresholds = widgets.card()
    threshold_layout = QFormLayout(thresholds)
    threshold_layout.setContentsMargins(22, 20, 22, 20)
    threshold_layout.setSpacing(14)
    app.review_input = QSpinBox()
    app.review_input.setRange(60, 100)
    app.review_input.setValue(app.rules.review_threshold)
    app.common_token_min_documents_input = QSpinBox()
    app.common_token_min_documents_input.setRange(1, 1000)
    app.common_token_min_documents_input.setValue(
        app.rules.common_token_min_documents
    )
    threshold_layout.addRow("Similarity review", app.review_input)
    threshold_layout.addRow(
        "Minimum common-token rows",
        app.common_token_min_documents_input,
    )
    outer.addWidget(thresholds)

    normalization = widgets.card()
    normalization_layout = QVBoxLayout(normalization)
    normalization_layout.setContentsMargins(22, 20, 22, 20)
    label = QLabel("Normalization")
    label.setObjectName("cardTitle")
    normalization_layout.addWidget(label)
    app.norm_inputs = {}
    for attribute, text in (
        ("lowercase", "Lowercase text"),
        ("remove_punctuation", "Remove punctuation"),
    ):
        control = QCheckBox(text)
        control.setChecked(getattr(app.rules, attribute))
        app.norm_inputs[attribute] = control
        normalization_layout.addWidget(control)
    outer.addWidget(normalization)

    actions = QHBoxLayout()
    actions.addStretch()
    actions.addWidget(
        widgets.button("Export JSON…", app.export_rules, "secondary")
    )
    actions.addWidget(
        widgets.button("Save settings", app.save_rules, "primary")
    )
    outer.addLayout(actions)
    outer.addStretch()
