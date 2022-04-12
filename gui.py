from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QFormLayout, QPushButton, QLineEdit, QMessageBox,
                               QListWidget, QFileDialog, QDialog, QDialogButtonBox,
                                QLabel, QProgressBar)

from PySide2.QtCore import Qt, QObject, QThread, Signal


import os
import requests
import aiohttp
import asyncio


class Worker(QObject):

    finished = Signal()
    progress = Signal(int)

    def __init__(self, urls):
        super(Worker, self).__init__()
        self.urls = urls
        self.total_size = []
        for url in self.urls:
            url_size = requests.get(url, stream=True).headers['content-length']
            if url_size is None:
                url_size = requests.get(url, stream=True).content
                self.total_size.append(int(len(url_size)))
            else:
                self.total_size.append(int(url_size))

        self._total_dl_size = sum(self.total_size)
        self.file_size = 0

    def download_files(self, url):

        file_name = url.split('/')[-1]
        file_name = f'{file_name}'

        with open(file_name, 'w+b', buffering=0) as file:
            print(f"Downloading {file_name}")
            downloaded_file = requests.get(url, stream=True)
            for chunk in downloaded_file.iter_content(8192):
                self.file_size += len(chunk)
                file.write(chunk)
                done = int(100 * self.file_size / self._total_dl_size)
                print("\r[%s%s]" % ('=' * done, ' ' * (100 - done)), end="")
                self.progress.emit(done)
            return print(f'{file_name} with {(self.file_size/1e3).__round__(2)} kB is downloaded...')


    def run(self):

        for url in self.urls:
            self.download_files(url)
        self.finished.emit()

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


        self.directory = os.path.expanduser('~/Downloads')

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
        self.directory = QFileDialog.getExistingDirectory(self, "Save To Directory", self.directory,
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

        if len(self.urls) == 0:
            QMessageBox.critical(self, "Error", "Please add links for download!")
        else:
            self.thread = QThread()
            # Step 3: Create a worker object
            self.worker = Worker(self.urls)
            # Step 4: Move worker to the thread
            self.worker.moveToThread(self.thread)
            # Step 5: Connect signals and slots
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            # Step 6: Start the thread
            self.thread.start()
            # Step 7: Disable buttons
            self.save_to_btn.setEnabled(False)
            self.add_link_btn.setEnabled(False)
            self.remove_link_btn.setEnabled(False)
            self.clear_all_btn.setEnabled(False)
            self.download_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            # Step 8: Connect signals
            self.worker.progress.connect(self.progress_list_message.setText("Status: Downloading in progress..."))
            self.worker.progress.connect(self.progress_bar.setValue)
            self.thread.finished.connect(lambda: self.save_to_btn.setEnabled(True))
            self.thread.finished.connect(lambda: self.add_link_btn.setEnabled(True))
            self.thread.finished.connect(lambda: self.remove_link_btn.setEnabled(True))
            self.thread.finished.connect(lambda: self.clear_all_btn.setEnabled(True))
            self.thread.finished.connect(lambda: self.download_btn.setEnabled(True))
            self.worker.finished.connect(lambda: self.progress_list_message.setText("Status: Downloading is finished!"))


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
        loop = asyncio.get_event_loop()
        if not self.add_link_form.text():
            QMessageBox.critical(self, "Error", "You must provide link!")
            return
        # Added check of link
        elif loop.run_until_complete(link_check(self.add_link_form.text())) > 400 and \
                loop.run_until_complete(link_check(self.add_link_form.text())) < 500:
            QMessageBox.critical(self, "Error", "Link is invalid!\nPlease check link and input correct one.")
            return
        # Link check done

        ### Example with requests significantly slower ###
        # elif requests.get(self.add_link_form.text()).status_code > 400 and \
        #         requests.get(self.add_link_form.text()).status_code < 500:
        #     QMessageBox.critical(self, "Error", "Link is invalid!\nPlease check link and input correct one.")
        #     return

        self.data = self.add_link_form.text()
        super().accept()


async def link_check(url):

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])

    return response.status
