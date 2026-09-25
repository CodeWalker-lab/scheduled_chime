import datetime
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import winsound


# PyInstallerの一時フォルダ内を参照するための関数（安全版）
def resource_path(relative_path):
    """実行環境（通常実行 or PyInstaller化後）に応じて正しいファイルパスを返す"""
    # getattrを使って安全に _MEIPASS を取得（存在しない場合は現在のディレクトリパス）
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class ChimeApp:

    def __init__(self, root):
        self.root = root

        # --- タイトルとバージョン表記 ---
        APP_VERSION = "v0.0"
        self.root.title(f"講習用チャイム   {APP_VERSION}")
        self.root.geometry("310x300")

        # --- ウィンドウ左上のアイコン設定 ---
        ico_path = resource_path("myicon.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass  # 万が一読み込みエラーが発生しても無視して動作継続

        # --- 1. WAVファイル選択エリア ---
        tk.Label(root, text="音源 (.wav)").pack(pady=(4, 0))

        file_frame = tk.Frame(root)
        file_frame.pack(pady=1)

        self.file_entry = tk.Entry(file_frame, width=28)
        self.file_entry.pack(side=tk.LEFT, padx=(0, 2))

        self.browse_button = tk.Button(
            file_frame, text="参照...", command=self.select_file
        )
        self.browse_button.pack(side=tk.LEFT)

        # --- 2. 時刻設定エリア（2列 × 6行） ---
        tk.Label(root, text="時刻 (HH:MM)").pack(pady=(4, 0))

        times_frame = tk.Frame(root)
        times_frame.pack(pady=1)

        self.time_entries = []
        default_times = [
            "09:10",
            "10:00",
            "10:10",
            "11:00",
            "11:10",
            "12:00",
            "13:10",
            "14:00",
            "14:10",
            "15:00",
            "15:10",
            "16:00",
        ]

        for i in range(12):
            col = 0 if i < 6 else 1
            row = i if i < 6 else i - 6

            lbl = tk.Label(
                times_frame, text=f"{i+1:2d}:", font=("Helvetica", 9)
            )
            lbl.grid(row=row, column=col * 2, padx=(2, 0), pady=0, sticky="e")

            entry = tk.Entry(
                times_frame, font=("Helvetica", 9), justify="center", width=6
            )
            entry.insert(0, default_times[i])
            entry.grid(row=row, column=col * 2 + 1, padx=(0, 4), pady=0)

            self.time_entries.append(entry)

        # --- 3. 予約ボタン（トグル切り替え対応）・状態表示 ---
        self.toggle_button = tk.Button(
            root, text="タイマー開始", command=self.toggle_timer, bg="#e1e1e1"
        )
        self.toggle_button.pack(pady=4)

        self.status_label = tk.Label(
            root, text="待機中", fg="gray", font=("Helvetica", 9)
        )
        self.status_label.pack(pady=(0, 2))

        self.is_running = False

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="WAVファイルを選択",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

    def toggle_timer(self):
        if self.is_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        wav_path = self.file_entry.get().strip()

        if wav_path and not os.path.exists(wav_path):
            messagebox.showerror(
                "エラー", "指定されたWAVファイルが存在しません。"
            )
            return

        target_times = []
        for i, entry in enumerate(self.time_entries):
            val = entry.get().strip()
            if not val:
                continue
            if len(val) == 4 and val[1] == ":":
                val = "0" + val

            try:
                datetime.datetime.strptime(val, "%H:%M")
                target_times.append(val)
            except ValueError:
                messagebox.showerror(
                    "エラー",
                    f"{i+1}番目の時刻「{val}」は正しい形式 (HH:MM) ではありません。",
                )
                return

        if not target_times:
            messagebox.showerror("エラー", "時刻が1つも入力されていません。")
            return

        self.is_running = True
        self.toggle_button.config(text="タイマー停止", bg="#ffcccc")

        count = len(target_times)
        self.status_label.config(
            text=f"{count} 個のタイマーを開始しました...", fg="green"
        )

        threading.Thread(
            target=self.check_time, args=(target_times, wav_path), daemon=True
        ).start()

    def stop_timer(self):
        self.is_running = False
        self.toggle_button.config(text="タイマー開始", bg="#e1e1e1")
        self.status_label.config(
            text="全てのタイマーを停止しました", fg="red"
        )

    def check_time(self, target_times, wav_path):
        played_times = set()

        while self.is_running:
            now = datetime.datetime.now().strftime("%H:%M")

            if now in target_times and now not in played_times:
                self.play_chime(wav_path)
                played_times.add(now)
                self.status_label.config(
                    text=f"【{now}】 チャイムを鳴らしました", fg="blue"
                )

            if len(played_times) >= len(target_times):
                self.status_label.config(
                    text="設定した全時刻のチャイムが完了しました",
                    fg="black",
                )
                self.is_running = False
                self.toggle_button.config(
                    text="タイマー開始", bg="#e1e1e1"
                )
                break

            time.sleep(1)

    def play_chime(self, wav_path):
        if wav_path:
            winsound.PlaySound(
                wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChimeApp(root)
    root.mainloop()