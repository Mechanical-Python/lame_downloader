from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QFormLayout, QPushButton, QLineEdit, QMessageBox,
                               QListWidget, QFileDialog, QDialog, QDialogButtonBox,
                                QLabel, QProgressBar)
from PySide2.QtCore import Qt


import os
import requests

import concurrent.futures


class MainWindow(QMainWindow):

    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.setWindowTitle("LameDownloader")
        self.setFixedSize(500, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.setupUI()

    def setupUI(self):
        # Set list view
        self.list_widget = QListWidget()
        self.progress_list_message = QLabel()
        self.progress_list_message.setText("Status: ...")

        self.urls = []
        self.progress_counter = []

        self.save_to_btn = QPushButton("Save To")
        self.add_link_btn = QPushButton("Add link")
        self.remove_link_btn = QPushButton("Remove link")
        self.download_btn = QPushButton("Download")
        self.clear_all_btn = QPushButton("Clear all")

        # Set layout 1
        layout_1 = QVBoxLayout()
        layout_1.addWidget(self.list_widget)
        layout_1.addWidget(self.progress_list_message)
        layout_1.addWidget(self.progress_bar)


        # Set layout 2
        layout_2 = QVBoxLayout()
        layout_2.addWidget(self.save_to_btn)
        layout_2.addWidget(self.add_link_btn)
        layout_2.addWidget(self.remove_link_btn)
        layout_2.addWidget(self.clear_all_btn)
        layout_2.addStretch()
        layout_2.addWidget(self.download_btn)



        self.layout.addLayout(layout_1)
        self.layout.addLayout(layout_2)

        self.save_to_btn.clicked.connect(self.save_to)
        self.add_link_btn.clicked.connect(self.add_link)
        self.remove_link_btn.clicked.connect(self.remove_link)
        self.clear_all_btn.clicked.connect(self.clear_all)
        self.download_btn.clicked.connect(self.download)



        self.directory = '/home/machine/Downloads'

    # GUI related functions

    def add_link(self):
        dialog = AddLinkDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.list_widget.addItem(dialog.data)
            self.urls.append(dialog.data)
            self.list_widget.show()

    def remove_link(self):
        if self.list_widget.count() == 0:
            QMessageBox.information(self, "Info", "There is no link to remove!")
        elif self.list_widget.count() == 1 and self.remove_link_btn.isDown() == False:
            self.progress_list_message.setText("Status: ...")
            self.progress_bar.setValue(0)
            self.progress_counter = []
            row = self.list_widget.currentRow()
            self.list_widget.takeItem(row)
            value = self.urls[row]
            self.urls.remove(value)
        else:
            self.progress_list_message.setText("Status: ...")
            self.progress_bar.setValue(0)
            self.progress_counter = []
            row = self.list_widget.currentRow()
            self.list_widget.takeItem(row)
            value = self.urls[row]
            self.urls.remove(value)


    def save_to(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Save To Directory", "/home/machine/Downloads",
                                                     QFileDialog.ShowDirsOnly|QFileDialog.DontResolveSymlinks)
        return self.directory

    def clear_all(self):
        if self.list_widget.count() == 0:
            QMessageBox.information(self, "Info", "There is nothing to clear!")
        else:
            self.list_widget.clear()
            self.progress_list_message.setText("Status: ...")
            self.progress_bar.setValue(0)
            self.urls = []
            self.progress_counter = []

    def download(self):
        os.chdir(self.directory)
        self.progress_list_message.setText("Status: ...")

        if len(self.urls) == 0:
            QMessageBox.critical(self, "Error", "Please add links for download!")
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.download_files, self.urls)

            self.progress_list_message.setText("Status: Files are downloaded!")


    # Download function

    def download_files(self, url):
        downloaded_file = requests.get(url).content

        file_name = url.split('/')[-1]
        file_name = f'{file_name}'

        value = 100 / self.list_widget.count()
        try:
            with open(file_name, 'w+b', buffering=0) as file:
                file.write(downloaded_file)
                file.flush()
                file.close()

            self.progress_counter.append(value)
            self.progress_bar.setValue(sum(self.progress_counter))
        finally:
            message = f'Status: {file_name} is downloaded...'
            self.progress_list_message.setText(message)

            return (f'{file_name} is downloaded...')



class AddLinkDialog(QDialog):

    def __init__(self, parent= None):
        super().__init__(parent=parent)
        self.setFixedSize(500, 100)
        self.setWindowTitle("Add link")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setupUI()

    def setupUI(self):
        # Add form layout
        self.add_link_form = QLineEdit()
        self.add_link_form.setObjectName("Add URL link")
        # Add Dialog standard buttons
        self.ButtonsBox = QDialogButtonBox(self)
        self.ButtonsBox.setOrientation(Qt.Horizontal)
        self.ButtonsBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.ButtonsBox.accepted.connect(self.accept)
        self.ButtonsBox.rejected.connect(self.reject)
        layout = QFormLayout()
        layout.addRow("Add URL Link", self.add_link_form)
        self.layout.addLayout(layout)
        self.layout.addWidget(self.ButtonsBox)

    def accept(self):
        """Accept the data provided through the dialog."""
        self.data = None
        if not self.add_link_form.text():
            QMessageBox.critical(self, "Error", "You must provide link!")
            return
        self.data = self.add_link_form.text()
        super().accept()


