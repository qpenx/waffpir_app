import sys
import os
import sqlite3
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QDateEdit
)
from PyQt5.QtGui import QFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyQt5.QtCore import QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class WaffpirApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(\"WAFFPİR Şube Programı\")
        self.setGeometry(200, 100, 1000, 800)
        self.setStyleSheet(\"background-color: #1e1e1e; color: white;\")

        self.veritabani_olustur()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_gelir_tab()
        self.init_liste_tab()
        self.init_gider_tab()
        self.init_gider_liste_tab()
        self.init_ozet_tab()
        self.init_grafik_tab()
    def veritabani_olustur(self):
        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gelirler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT,
                sube TEXT,
                kaynak TEXT,
                bruttutar REAL,
                nettutar REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giderler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT,
                sube TEXT,
                kategori TEXT,
                tutar REAL
            )
        ''')
        conn.commit()
        conn.close()

    def init_gelir_tab(self):
        gelir_tab = QWidget()
        layout = QVBoxLayout()

        self.sube_combo = QComboBox()
        self.sube_combo.addItems(["Maltepe", "İçerenköy", "Esatpaşa"])
        self.kaynak_combo = QComboBox()
        self.kaynak_combo.addItems([
            "Yemeksepeti %10", "Yemeksepeti %35", "Trendyol %11", "Trendyol %35",
            "Getir %10", "Getir %35", "Migros %9", "Migros %35", "Masa", "Alo Paket"
        ])
        self.tutar_input = QLineEdit()
        self.net_label = QLabel("Net Tutar: ₺0")
        ekle_btn = QPushButton("Geliri Kaydet")
        ekle_btn.clicked.connect(self.gelir_ekle)

        layout.addWidget(QLabel("Şube:"))
        layout.addWidget(self.sube_combo)
        layout.addWidget(QLabel("Kaynak:"))
        layout.addWidget(self.kaynak_combo)
        layout.addWidget(QLabel("Brüt Tutar:"))
        layout.addWidget(self.tutar_input)
        layout.addWidget(self.net_label)
        layout.addWidget(ekle_btn)

        self.kaynak_combo.currentIndexChanged.connect(self.net_tutar_hesapla)
        self.tutar_input.textChanged.connect(self.net_tutar_hesapla)

        gelir_tab.setLayout(layout)
        self.tabs.addTab(gelir_tab, "Gelir Girişi")
    def init_liste_tab(self):
        liste_tab = QWidget()
        layout = QVBoxLayout()

        self.tarih_basla = QDateEdit()
        self.tarih_basla.setCalendarPopup(True)
        self.tarih_basla.setDate(QDate.currentDate().addMonths(-1))

        self.tarih_bitis = QDateEdit()
        self.tarih_bitis.setCalendarPopup(True)
        self.tarih_bitis.setDate(QDate.currentDate())

        self.filtre_sube = QComboBox()
        self.filtre_sube.addItem("Tüm Şubeler")
        self.filtre_sube.addItems(["Maltepe", "İçerenköy", "Esatpaşa"])

        filtre_btn = QPushButton("Filtrele")
        filtre_btn.clicked.connect(self.kayitlari_getir)

        filtre_layout = QHBoxLayout()
        filtre_layout.addWidget(QLabel("Başlangıç Tarihi:"))
        filtre_layout.addWidget(self.tarih_basla)
        filtre_layout.addWidget(QLabel("Bitiş Tarihi:"))
        filtre_layout.addWidget(self.tarih_bitis)
        filtre_layout.addWidget(QLabel("Şube:"))
        filtre_layout.addWidget(self.filtre_sube)
        filtre_layout.addWidget(filtre_btn)

        layout.addLayout(filtre_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tarih", "Şube", "Kaynak", "Brüt ₺", "Net ₺"])
        layout.addWidget(self.table)

        liste_tab.setLayout(layout)
        self.tabs.addTab(liste_tab, "Gelir Kayıtları")

    def net_tutar_hesapla(self):
        try:
            brüt = float(self.tutar_input.text())
        except:
            brüt = 0.0

        kaynak = self.kaynak_combo.currentText()
        oran = 0
        if "%" in kaynak:
            try:
                oran = int(kaynak.split("%")[1])
            except:
                oran = 0
        net = brüt - (brüt * oran / 100)
        self.net_label.setText(f"Net Tutar: ₺{net:.2f}")

    def gelir_ekle(self):
        tarih = datetime.datetime.now().strftime("%Y-%m-%d")
        sube = self.sube_combo.currentText()
        kaynak = self.kaynak_combo.currentText()
        try:
            bruttutar = float(self.tutar_input.text())
        except:
            QMessageBox.warning(self, "Hata", "Geçerli bir tutar gir.")
            return

        oran = 0
        if "%" in kaynak:
            try:
                oran = int(kaynak.split("%")[1])
            except:
                oran = 0

        nettutar = bruttutar - (bruttutar * oran / 100)

        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gelirler (tarih, sube, kaynak, bruttutar, nettutar)
            VALUES (?, ?, ?, ?, ?)
        ''', (tarih, sube, kaynak, bruttutar, nettutar))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Başarılı", "Gelir başarıyla kaydedildi!")
        self.tutar_input.clear()
        self.net_label.setText("Net Tutar: ₺0")
    def init_gider_tab(self):
        gider_tab = QWidget()
        layout = QVBoxLayout()

        self.gider_tarih = QDateEdit()
        self.gider_tarih.setCalendarPopup(True)
        self.gider_tarih.setDate(QDate.currentDate())

        self.gider_sube_combo = QComboBox()
        self.gider_sube_combo.addItems(["Maltepe", "İçerenköy", "Esatpaşa"])

        self.gider_kategori = QComboBox()
        self.gider_kategori.addItems(["Kira", "Maaş", "Malzeme", "Market", "Kişisel", "Komisyon", "Pay Ücreti", "Kurye"])

        self.gider_tutar_input = QLineEdit()

        gider_ekle_btn = QPushButton("Gideri Kaydet")
        gider_ekle_btn.clicked.connect(self.gider_ekle)

        layout.addWidget(QLabel("Tarih:"))
        layout.addWidget(self.gider_tarih)
        layout.addWidget(QLabel("Şube:"))
        layout.addWidget(self.gider_sube_combo)
        layout.addWidget(QLabel("Kategori:"))
        layout.addWidget(self.gider_kategori)
        layout.addWidget(QLabel("Tutar (₺):"))
        layout.addWidget(self.gider_tutar_input)
        layout.addWidget(gider_ekle_btn)

        gider_tab.setLayout(layout)
        self.tabs.addTab(gider_tab, "Gider Girişi")

    def gider_ekle(self):
        tarih = self.gider_tarih.date().toString("yyyy-MM-dd")
        sube = self.gider_sube_combo.currentText()
        kategori = self.gider_kategori.currentText()
        try:
            tutar = float(self.gider_tutar_input.text())
        except:
            QMessageBox.warning(self, "Hata", "Geçerli bir tutar gir.")
            return

        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO giderler (tarih, sube, kategori, tutar)
            VALUES (?, ?, ?, ?)
        ''', (tarih, sube, kategori, tutar))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Başarılı", "Gider kaydedildi.")
        self.gider_tutar_input.clear()

    def init_gider_liste_tab(self):
        gider_liste_tab = QWidget()
        layout = QVBoxLayout()

        self.gider_table = QTableWidget()
        self.gider_table.setColumnCount(4)
        self.gider_table.setHorizontalHeaderLabels(["Tarih", "Şube", "Kategori", "Tutar ₺"])
        layout.addWidget(self.gider_table)

        yenile_btn = QPushButton("Giderleri Yenile")
        yenile_btn.clicked.connect(self.gider_kayitlari_getir)
        layout.addWidget(yenile_btn)

        gider_liste_tab.setLayout(layout)
        self.tabs.addTab(gider_liste_tab, "Gider Kayıtları")

    def gider_kayitlari_getir(self):
        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT tarih, sube, kategori, tutar FROM giderler ORDER BY id DESC")
        veriler = cursor.fetchall()
        conn.close()

        self.gider_table.setRowCount(len(veriler))
        for i, satir in enumerate(veriler):
            for j, deger in enumerate(satir):
                self.gider_table.setItem(i, j, QTableWidgetItem(str(deger)))
    def kayitlari_getir(self):
        basla = self.tarih_basla.date().toString("yyyy-MM-dd")
        bitis = self.tarih_bitis.date().toString("yyyy-MM-dd")
        sube = self.filtre_sube.currentText()

        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        if sube == "Tüm Şubeler":
            cursor.execute("""
                SELECT tarih, sube, kaynak, bruttutar, nettutar
                FROM gelirler
                WHERE tarih BETWEEN ? AND ?
                ORDER BY id DESC
            """, (basla, bitis))
        else:
            cursor.execute("""
                SELECT tarih, sube, kaynak, bruttutar, nettutar
                FROM gelirler
                WHERE tarih BETWEEN ? AND ? AND sube = ?
                ORDER BY id DESC
            """, (basla, bitis, sube))

        veriler = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(veriler))
        for i, satir in enumerate(veriler):
            for j, deger in enumerate(satir):
                self.table.setItem(i, j, QTableWidgetItem(str(deger)))

    def init_ozet_tab(self):
        ozet_tab = QWidget()
        layout = QVBoxLayout()

        self.ozet_tarih = QDateEdit()
        self.ozet_tarih.setCalendarPopup(True)
        self.ozet_tarih.setDate(QDate.currentDate())

        hesapla_btn = QPushButton("Aylık Özeti Göster")
        hesapla_btn.clicked.connect(self.ozet_hesapla)

        self.ozet_label = QLabel("Toplam Gelir: ₺0\nToplam Gider: ₺0\nNet Kar/Zarar: ₺0")

        layout.addWidget(QLabel("Tarih Seç (Ay):"))
        layout.addWidget(self.ozet_tarih)
        layout.addWidget(hesapla_btn)
        layout.addWidget(self.ozet_label)

        ozet_tab.setLayout(layout)
        self.tabs.addTab(ozet_tab, "Aylık Özet")

    def ozet_hesapla(self):
        secilen = self.ozet_tarih.date()
        yil = secilen.year()
        ay = secilen.month()
        ay_baslangic = f"{yil}-{ay:02d}-01"
        if ay == 12:
            ay_bitis = f"{yil+1}-01-01"
        else:
            ay_bitis = f"{yil}-{ay+1:02d}-01"

        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(nettutar) FROM gelirler WHERE tarih >= ? AND tarih < ?", (ay_baslangic, ay_bitis))
        toplam_gelir = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(tutar) FROM giderler WHERE tarih >= ? AND tarih < ?", (ay_baslangic, ay_bitis))
        toplam_gider = cursor.fetchone()[0] or 0

        net = toplam_gelir - toplam_gider
        self.ozet_label.setText(
            f"Toplam Gelir: ₺{toplam_gelir:.2f}\nToplam Gider: ₺{toplam_gider:.2f}\nNet Kar/Zarar: ₺{net:.2f}"
        )
        conn.close()

    def init_grafik_tab(self):
        grafik_tab = QWidget()
        layout = QVBoxLayout()

        self.grafik_tarih = QDateEdit()
        self.grafik_tarih.setCalendarPopup(True)
        self.grafik_tarih.setDate(QDate.currentDate())

        grafik_btn = QPushButton("Grafiği Göster")
        grafik_btn.clicked.connect(self.grafik_olustur)

        self.figure = plt.figure(facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(QLabel("Grafik için Ay Seç:"))
        layout.addWidget(self.grafik_tarih)
        layout.addWidget(grafik_btn)
        layout.addWidget(self.canvas)

        grafik_tab.setLayout(layout)
        self.tabs.addTab(grafik_tab, "Gelir/Gider Grafiği")

    def grafik_olustur(self):
        secilen = self.grafik_tarih.date()
        yil = secilen.year()
        ay = secilen.month()
        ay_baslangic = f"{yil}-{ay:02d}-01"
        ay_bitis = f"{yil+1}-01-01" if ay == 12 else f"{yil}-{ay+1:02d}-01"

        conn = sqlite3.connect("waffpir_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(nettutar) FROM gelirler WHERE tarih >= ? AND tarih < ?", (ay_baslangic, ay_bitis))
        gelir = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(tutar) FROM giderler WHERE tarih >= ? AND tarih < ?", (ay_baslangic, ay_bitis))
        gider = cursor.fetchone()[0] or 0
        conn.close()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(["Gelir", "Gider"], [gelir, gider], color=["#4caf50", "#f44336"])
        ax.set_title("Aylık Gelir vs Gider", color="white")
        ax.set_facecolor("#2e2e2e")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        for spine in ax.spines.values():
            spine.set_color("white")
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WaffpirApp()
    window.show()
    sys.exit(app.exec_())

