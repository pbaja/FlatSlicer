

if __name__ == '__main__':

    # Display splash screen
    import tkinter as tk
    splash = tk.Tk()
    splash.tk_setPalette(background='#222', foreground='#FFF')
    splash.title("FlatSlicer")
    splash.overrideredirect(True)

    w,h = 400, 200
    sw,sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    x,y = int(sw/2 - w/2), int(sh/2 - h/2)
    splash.geometry(f"{w}x{h}+{x}+{y}")

    # Splash text
    import random
    texts = ["Starting up", "Becoming alive", "Burning eyes out", "Adding red flags", "Looking into the beam"]
    font_name = 'Segoe UI, Ubuntu, sans-serif'
    tk.Label(splash, text="FlatSlicer", fg='#65AED9', font=(font_name, 40)).pack(expand=True, fill=tk.BOTH)
    tk.Label(splash, text=random.choice(texts) + '...', font=(font_name, 10)).pack(expand=True, fill=tk.BOTH)
    splash.update()
    splash.update_idletasks()

    # Load app
    import app

    # Run app
    app.run(on_ready=lambda: splash.destroy())