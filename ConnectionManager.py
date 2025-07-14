import tkinter as tk
from tkinter import messagebox
import psutil
import platform
import subprocess

class ConnectionManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Connection Manager")

        self.refresh_btn = tk.Button(root, text="Refresh", command=self.refresh_connections)
        self.refresh_btn.pack(pady=5)

        self.conn_listbox = tk.Listbox(root, width=100)
        self.conn_listbox.pack(padx=10, pady=5)

        self.disconnect_btn = tk.Button(root, text="Disconnect Port", command=self.disconnect_port)
        self.disconnect_btn.pack(pady=5)

        self.block_btn = tk.Button(root, text="Block Port", command=self.block_port)
        self.block_btn.pack(pady=5)

        self.refresh_connections()

    def refresh_connections(self):
        self.conn_listbox.delete(0, tk.END)
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                item = f"PID: {conn.pid} | {conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port}"
                self.conn_listbox.insert(tk.END, item)

    def get_selected_port(self):
        try:
            selected = self.conn_listbox.get(self.conn_listbox.curselection())
            port = int(selected.split(":")[1].split(" ")[0])
            return port
        except:
            messagebox.showwarning("No selection", "Please select a connection.")
            return None

    def disconnect_port(self):
        port = self.get_selected_port()
        if port is None:
            return
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.pid:
                try:
                    p = psutil.Process(conn.pid)
                    p.terminate()
                    messagebox.showinfo("Disconnected", f"Terminated process {conn.pid} using port {port}")
                    self.refresh_connections()
                    return
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to terminate process: {e}")
                    return
        messagebox.showinfo("Not Found", "No process found using selected port.")

    def block_port(self):
        port = self.get_selected_port()
        if port is None:
            return
        os_name = platform.system()

        try:
            if os_name == "Windows":
                subprocess.run(f'netsh advfirewall firewall add rule name="BlockPort{port}" dir=in action=block protocol=TCP localport={port}', shell=True)
                messagebox.showinfo("Blocked", f"Port {port} blocked using Windows Firewall.")
            elif os_name == "Linux":
                subprocess.run(f'sudo iptables -A INPUT -p tcp --dport {port} -j DROP', shell=True)
                messagebox.showinfo("Blocked", f"Port {port} blocked using iptables.")
            else:
                messagebox.showwarning("Unsupported", f"Blocking not implemented for {os_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to block port: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectionManagerApp(root)
    root.mainloop()
