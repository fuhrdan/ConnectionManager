import socket
import tkinter as tk
from tkinter import messagebox
import psutil
import platform
import subprocess
from threading import Thread
from time import sleep

from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw

class ConnectionManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Connection Manager")

        self.conn_listbox = tk.Listbox(root, width=120, height=25)
        self.conn_listbox.pack(padx=10, pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        tk.Button(self.button_frame, text="Disconnect Port", command=self.disconnect_port).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Block Port", command=self.block_port).pack(side=tk.LEFT, padx=5)

        self.running = True
        self.auto_refresh_thread = Thread(target=self.auto_refresh_loop, daemon=True)
        self.auto_refresh_thread.start()

        self.setup_system_tray()

        self.refresh_connections()

    def setup_system_tray(self):
        def create_image():
            img = Image.new('RGB', (64, 64), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle((16, 16, 48, 48), fill='green')
            return img

        self.icon = Icon("conn_mgr", create_image(), menu=Menu(
            item("Show/Hide", self.toggle_visibility),
            item("Exit", self.exit_app)
        ))

        def tray_thread():
            self.icon.run()

        Thread(target=tray_thread, daemon=True).start()

    def toggle_visibility(self):
        if self.root.winfo_viewable():
            self.root.withdraw()
        else:
            self.root.deiconify()

    def exit_app(self):
        self.running = False
        self.icon.stop()
        self.root.quit()

    def auto_refresh_loop(self):
        while self.running:
            self.refresh_connections()
            sleep(5)  # Refresh every 5 seconds

    def refresh_connections(self):
        try:
            self.conn_listbox.delete(0, tk.END)
            conns = psutil.net_connections(kind='inet')
            for conn in conns:
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                status = conn.status if conn.status else "NONE"
                proto = "UDP" if conn.type == socket.SOCK_DGRAM else "TCP"
                pid = conn.pid if conn.pid else "-"
                item = f"{proto} | PID: {pid} | {laddr} -> {raddr} | Status: {status}"
                self.conn_listbox.insert(tk.END, item)
        except Exception as e:
            print(f"Refresh error: {e}")

    def get_selected_port(self):
        try:
            selected = self.conn_listbox.get(self.conn_listbox.curselection())
            lport = int(selected.split(":")[1].split(" ")[0])
            proto = "udp" if "UDP" in selected else "tcp"
            return lport, proto
        except:
            messagebox.showwarning("No selection", "Please select a connection.")
            return None, None

    def disconnect_port(self):
        port, _ = self.get_selected_port()
        if port is None:
            return
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.pid:
                try:
                    psutil.Process(conn.pid).terminate()
                    messagebox.showinfo("Disconnected", f"Terminated process {conn.pid} using port {port}")
                    return
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to terminate process: {e}")
                    return
        messagebox.showinfo("Not Found", "No process found using selected port.")

    def block_port(self):
        port, proto = self.get_selected_port()
        if port is None:
            return
        os_name = platform.system()

        try:
            if os_name == "Windows":
                subprocess.run(
                    f'netsh advfirewall firewall add rule name="BlockPort{port}" '
                    f'dir=in action=block protocol={proto.upper()} localport={port}',
                    shell=True
                )
                messagebox.showinfo("Blocked", f"Port {port} ({proto.upper()}) blocked using Windows Firewall.")
            elif os_name == "Linux":
                subprocess.run(f'sudo iptables -A INPUT -p {proto} --dport {port} -j DROP', shell=True)
                messagebox.showinfo("Blocked", f"Port {port} ({proto}) blocked using iptables.")
            else:
                messagebox.showwarning("Unsupported", f"Blocking not implemented for {os_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to block port: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectionManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.toggle_visibility)  # Minimize to tray on close
    root.mainloop()
