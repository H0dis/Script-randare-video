# Program de inlocuire perspectiva pe ecran verde
# ------------------------------------------------
# Acest program detecteaza un dreptunghi verde intr-un videoclip
# si il inlocuieste cu o imagine selectata, respectand perspectiva.
# Include interfata grafica cu: incarcare imagine PNG/JPG,
# incarcare videoclip si procesare video completa cu rezultat final.

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from threading import Thread
from tkinter import ttk

overlay_path = None
video_path = None
progress_var = None
progress_bar = None
output_filename = None

# Intervalul de detectie pentru verde (in HSV)
lower_green = np.array([35, 40, 40])
upper_green = np.array([85, 255, 255])

# Functie care ordoneaza punctele dreptunghiului (pt. perspectiva corecta)
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

# Aplica imaginea peste patratul verde, cu perspectiva
def apply_overlay(frame, overlay_img):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return frame

    largest = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, epsilon, True)

    if len(approx) != 4:
        return frame

    pts_dst = order_points(np.array([p[0] for p in approx], dtype="float32"))
    h_ol, w_ol = overlay_img.shape[:2]
    pts_src = np.array([[0, 0], [w_ol, 0], [w_ol, h_ol], [0, h_ol]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)

    if overlay_img.shape[2] == 4:
        b, g, r, a = cv2.split(overlay_img)
        overlay_rgb = cv2.merge((b, g, r))
        warped_overlay = cv2.warpPerspective(overlay_rgb, matrix, (frame.shape[1], frame.shape[0]))
        warped_alpha = cv2.warpPerspective(a, matrix, (frame.shape[1], frame.shape[0]))
        mask_overlay = warped_alpha
    else:
        warped_overlay = cv2.warpPerspective(overlay_img, matrix, (frame.shape[1], frame.shape[0]))
        mask_overlay = np.any(warped_overlay != [0, 0, 0], axis=-1).astype(np.uint8) * 255

    mask_inv = cv2.bitwise_not(mask_overlay)
    fg = cv2.bitwise_and(warped_overlay, warped_overlay, mask=mask_overlay)
    bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    return cv2.add(fg, bg)

# Procesare video completa (salveaza in fisier .mp4)
def proceseaza():
    if not overlay_path or not video_path:
        print("Selecteaza un video si o imagine.")
        return
    overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    filename = output_filename.get().strip() or "output_final"
    out = cv2.VideoWriter(f"{filename}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        result = apply_overlay(frame, overlay)
        out.write(result)
        count += 1
        progress = int((count / total_frames) * 100)
        progress_var.set(progress)
        progress_bar.update_idletasks()

    cap.release()
    out.release()
    progress_var.set(100)
    print("Exportat: output_final.mp4")

# Selecteaza imaginea PNG/JPG
def incarca_png():
    global overlay_path
    overlay_path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])

def incarca_jpg():
    global overlay_path
    overlay_path = filedialog.askopenfilename(filetypes=[("JPG", "*.jpg")])

# Selecteaza videoclipul MP4
def incarca_video():
    global video_path
    video_path = filedialog.askopenfilename(filetypes=[("MP4", "*.mp4")])

# Setare interfata
root = tk.Tk()
root.title("Procesare vidoclip vinyluri © Hodis Florin")
root.geometry("480x300")

frame_controls = tk.Frame(root)
frame_controls.pack(padx=20, pady=20)

btn1 = tk.Button(frame_controls, text="Incarca poza PNG", width=30, command=incarca_png)
btn2 = tk.Button(frame_controls, text="Incarca poza JPG", width=30, command=incarca_jpg)
btn_video = tk.Button(frame_controls, text="Incarca videoclip", width=30, command=incarca_video)
btn_proc = tk.Button(frame_controls, text="Proceseaza video complet", width=30, command=lambda: Thread(target=proceseaza).start())

entry_label = tk.Label(frame_controls, text="Nume fisier(fara extensie) default e output_final:")
entry_label.pack(pady=(10, 0))
output_filename = tk.Entry(frame_controls, width=30)
output_filename.insert(0, "output_final")  # valoare implicită
output_filename.pack(pady=(0, 10))

btn1.pack(pady=5)
btn2.pack(pady=5)
btn_video.pack(pady=10)
btn_proc.pack(pady=5)

# Bara de progres
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.pack(pady=5)

root.mainloop()

# ------------------------------------------------
# README:
# 1. Ruleaza scriptul si incarca un videoclip (ex: scena_verde.mp4).
# 2. Apasa "Incarca poza PNG/JPG" pentru a selecta o imagine de coperta.
# 3. Apasa "Proceseaza video complet" pentru a genera fisierul final .mp4.
# Necesita: OpenCV (cv2), Pillow (PIL), tkinter (standard in Python).
# 4. Asigura-te ca ai instalat dependintele necesare:
#    pip install opencv-python opencv-python-headless numpy pillow
# 5. Fisierul rezultat va fi salvat ca "output_final.mp4" in acelasi director.
# ------------------------------------------------
