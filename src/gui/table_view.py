from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class TableView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QTableView { font-size: 10pt; }")
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_data(self, data, row_labels=None, column_labels=None):
        self.clear()
        if not data:
            return

        if isinstance(data[0], list):  # 2D data
            self.setRowCount(len(data))
            self.setColumnCount(len(data[0]))
        else:  # 1D data
            self.setRowCount(1)
            self.setColumnCount(len(data))

        for i, row in enumerate(data):
            if isinstance(row, list):
                for j, value in enumerate(row):
                    self.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                self.setItem(0, i, QTableWidgetItem(str(row)))

        if row_labels:
            self.setVerticalHeaderLabels(row_labels)
        if column_labels:
            self.setHorizontalHeaderLabels(column_labels)

    def clear_data(self):
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)
