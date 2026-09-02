"""Matching settings view."""

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
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
    threshold_layout = QVBoxLayout(thresholds)
    threshold_layout.setContentsMargins(22, 20, 22, 20)
    threshold_layout.setSpacing(14)
    threshold_title = QLabel("Thresholds")
    threshold_title.setObjectName("cardTitle")
    threshold_layout.addWidget(threshold_title)
    review_row, app.review_input = widgets.slider_row(
        "Similarity review",
        app.rules.review_threshold,
        60,
        100,
        suffix="%",
    )
    common_row, app.common_token_min_documents_input = widgets.slider_row(
        "Minimum common-token rows",
        app.rules.common_token_min_documents,
        1,
        1000,
    )
    threshold_layout.addWidget(review_row)
    threshold_layout.addWidget(common_row)
    outer.addWidget(thresholds)

    automatic = widgets.card()
    automatic_layout = QVBoxLayout(automatic)
    automatic_layout.setContentsMargins(22, 20, 22, 20)
    automatic_layout.setSpacing(12)
    automatic_title = QLabel("Automatic acceptance")
    automatic_title.setObjectName("cardTitle")
    automatic_layout.addWidget(automatic_title)
    app.auto_accept_input = QCheckBox(
        "Automatically merge high-confidence groups"
    )
    app.auto_accept_input.setChecked(app.rules.auto_accept)
    automatic_layout.addWidget(app.auto_accept_input)
    automatic_note = QLabel(
        "Groups at or above this score are merged without opening them "
        "in Review. They remain identified in the audit file."
    )
    automatic_note.setObjectName("muted")
    automatic_note.setWordWrap(True)
    automatic_layout.addWidget(automatic_note)
    auto_row, app.auto_accept_threshold_input = widgets.slider_row(
        "Auto-accept at",
        app.rules.auto_accept_threshold,
        60,
        100,
        suffix="%",
    )
    app.auto_accept_threshold_input.setEnabled(app.rules.auto_accept)
    app.auto_accept_input.toggled.connect(
        app.auto_accept_threshold_input.setEnabled
    )
    automatic_layout.addWidget(auto_row)
    outer.addWidget(automatic)

    normalization = widgets.card()
    normalization_layout = QVBoxLayout(normalization)
    normalization_layout.setContentsMargins(22, 20, 22, 20)
    label = QLabel("Normalization")
    label.setObjectName("cardTitle")
    normalization_layout.addWidget(label)
    app.lowercase_input = QCheckBox("Lowercase text")
    app.lowercase_input.setChecked(app.rules.lowercase)
    normalization_layout.addWidget(app.lowercase_input)
    app.remove_punctuation_input = QCheckBox("Remove punctuation")
    app.remove_punctuation_input.setChecked(app.rules.remove_punctuation)
    normalization_layout.addWidget(app.remove_punctuation_input)
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
