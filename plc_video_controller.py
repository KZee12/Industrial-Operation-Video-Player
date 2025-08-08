import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import threading
import time
import os
import sys
import shutil
from pathlib import Path
import ctypes

# 👉 Load snap7.dll manually from the current EXE folder (handles PyInstaller + raw)
def preload_snap7():
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        dll_path = os.path.join(sys._MEIPASS, "snap7.dll")
    else:
        # Running as raw script
        dll_path = os.path.join(os.path.dirname(__file__), "snap7.dll")

    try:
        ctypes.WinDLL(dll_path)
    except Exception as e:
        print(f"[ERROR] Failed to preload snap7.dll: {e}")
        raise

preload_snap7()

try:
    import snap7
    SNAP7_AVAILABLE = True
except ImportError:
    SNAP7_AVAILABLE = False

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False

class PLCVideoController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PLC Video Controller")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Simulation mode toggle
        self.simulation_mode = tk.BooleanVar(value=False)
        self.last_sim_command = 1

        # Application state
        self.plc_client = None
        self.video_player = None
        self.vlc_instance = None
        self.is_connected = False
        self.is_monitoring = False
        self.monitoring_thread = None
        self.video_mappings = {}
        self.current_video_index = -1
        self.app_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.videos_directory = os.path.join(self.app_directory, "videos")
        os.makedirs(self.videos_directory, exist_ok=True)

        # Load config and initialize VLC
        self.config = configparser.ConfigParser()
        self.load_config()
        if VLC_AVAILABLE:
            try:
                self.vlc_instance = vlc.Instance()
                self.video_player = self.vlc_instance.media_player_new()
            except:
                pass

        self.setup_gui()
        self.load_video_mappings()

    def load_config(self):
        config_path = os.path.join(self.app_directory, 'config.ini')
        if os.path.exists(config_path):
            self.config.read(config_path)
        else:
            self.config['PLC'] = {'ip_address':'192.168.1.100','rack':'0','slot':'1','db_number':'1'}
            with open(config_path,'w') as f: self.config.write(f)

    def setup_gui(self):
        main = ttk.Frame(self.root); main.pack(fill='both',expand=True,padx=10,pady=10)
        ttk.Label(main,text="PLC Video Controller",font=('Arial',16,'bold')).pack(pady=10)

        # Simulation
        sim_frame=ttk.LabelFrame(main,text="Simulation Mode"); sim_frame.pack(fill='x',pady=5)
        ttk.Checkbutton(sim_frame,text="Enable Simulation",variable=self.simulation_mode).pack(anchor='w',padx=5)
        sim_inner=ttk.Frame(sim_frame); sim_inner.pack(fill='x',pady=5)
        ttk.Label(sim_inner,text="Index:").pack(side='left')
        self.sim_index=ttk.Entry(sim_inner,width=5); self.sim_index.pack(side='left',padx=5)
        for cmd,label in [(1,"▶️ Play"),(2,"⏸️ Pause"),(3,"▶️ Resume"),(0,"⏹️ Stop")]:
            ttk.Button(sim_inner,text=label,command=lambda c=cmd: self.simulate_command(c)).pack(side='left',padx=5)

        # Status
        status=ttk.LabelFrame(main,text="Status"); status.pack(fill='x',pady=5)
        row=ttk.Frame(status); row.pack(fill='x')
        ttk.Label(row,text="Conn:").pack(side='left'); self.conn_lbl=ttk.Label(row,text="Disconnected",foreground="red"); self.conn_lbl.pack(side='left',padx=5)
        ttk.Label(row,text="Cmd:").pack(side='left'); self.cmd_lbl=ttk.Label(row,text="0"); self.cmd_lbl.pack(side='left',padx=5)
        ttk.Label(row,text="Idx:").pack(side='left'); self.idx_lbl=ttk.Label(row,text="0"); self.idx_lbl.pack(side='left',padx=5)

        # PLC Config & Controls
        cfg=ttk.LabelFrame(main,text="PLC Controls"); cfg.pack(fill='x',pady=5)
        e1=ttk.Frame(cfg); e1.pack(fill='x',pady=2)
        ttk.Label(e1,text="PLC IP:",width=10).pack(side='left'); self.ip_e=ttk.Entry(e1); self.ip_e.insert(0,self.config['PLC']['ip_address']); self.ip_e.pack(side='left',fill='x',expand=True,padx=5)
        e2=ttk.Frame(cfg); e2.pack(fill='x',pady=2)
        ttk.Label(e2,text="DB Num:",width=10).pack(side='left'); self.db_e=ttk.Entry(e2,width=5); self.db_e.insert(0,self.config['PLC']['db_number']); self.db_e.pack(side='left',padx=5)
        btns=ttk.Frame(cfg); btns.pack(fill='x',pady=5)
        ttk.Button(btns,text="Connect",command=self.toggle_connection).pack(side='left',padx=5)
        ttk.Button(btns,text="Start Monitoring",command=self.toggle_monitor, state='disabled').pack(side='left')

        # Video Mapping
        mapf=ttk.LabelFrame(main,text="Video Mapping"); mapf.pack(fill='both',expand=True,pady=5)
        ctrl=ttk.Frame(mapf); ctrl.pack(fill='x',pady=5)
        ttk.Label(ctrl,text="Index:").pack(side='left'); self.map_idx=ttk.Entry(ctrl,width=5); self.map_idx.pack(side='left',padx=5)
        ttk.Button(ctrl,text="Add Video",command=self.add_video_mapping).pack(side='left',padx=5)
        ttk.Button(ctrl,text="Remove Selected",command=self.remove_video_mapping).pack(side='left')
        cols=('Index','File'); self.tree=ttk.Treeview(mapf,columns=cols,show='headings'); self.tree.heading('Index',text='Index'); self.tree.heading('File',text='File'); self.tree.pack(fill='both',expand=True)

        # Current Video Display
        curf=ttk.LabelFrame(main,text="Current Video"); curf.pack(fill='x',pady=5)
        self.cur_lbl=ttk.Label(curf,text="None"); self.cur_lbl.pack()

    def simulate_command(self,c):
        if not self.simulation_mode.get():
            messagebox.showwarning("Simulation","Enable simulation first"); return
        try:
            idx=int(self.sim_index.get())
        except:
            messagebox.showerror("Error","Enter valid index");return
        self.handle_plc_command(c,idx)
        self.update_status(c,idx)

    def update_status(self,cmd,idx):
        txt={0:"Stop",1:"Play",2:"Pause",3:"Resume"}.get(cmd,"?") 
        self.cmd_lbl.config(text=f"{cmd}({txt})"); self.idx_lbl.config(text=str(idx))

    def handle_plc_command(self,cmd,idx):
        path=self.video_mappings.get(idx)
        if path and os.path.exists(path) and VLC_AVAILABLE:
            if idx!=self.current_video_index:
                media=self.vlc_instance.media_new(path)
                self.video_player.set_media(media); self.current_video_index=idx; self.cur_lbl.config(text=os.path.basename(path))
            if cmd==1: self.video_player.play()
            elif cmd==2: self.video_player.pause()
            elif cmd==3: self.video_player.play()
            elif cmd==0: self.video_player.stop()
        else:
            self.cur_lbl.config(text=f"No vid for idx {idx}")

    def toggle_connection(self):
        if self.is_connected: self.disconnect_plc()
        else: self.connect_plc()

    def connect_plc(self):
        if not SNAP7_AVAILABLE: messagebox.showerror("Error","Install python-snap7");return
        try:
            ip=self.ip_e.get().strip();db=int(self.db_e.get())
            c=snap7.client.Client();c.connect(ip,0,1);self.plc_client=c
            self.is_connected=True;self.conn_lbl.config(text="Connected",fg="green")
            self.root.nametowidget(".!frame.!labelframe2.!frame.!button2").config(state='normal')
        except Exception as e: messagebox.showerror("Conn Err",str(e))

    def disconnect_plc(self):
        if self.is_monitoring: self.toggle_monitor()
        if self.plc_client: self.plc_client.disconnect()
        self.is_connected=False;self.conn_lbl.config(text="Disconnected",fg="red")

    def toggle_monitor(self):
        btn=self.root.nametowidget(".!frame.!labelframe2.!frame.!button2")
        if self.is_monitoring:
            self.is_monitoring=False;btn.config(text="Start Monitoring")
        else:
            self.is_monitoring=True;btn.config(text="Stop Monitoring");threading.Thread(target=self.monitor_loop,daemon=True).start()

    def monitor_loop(self):
        while self.is_monitoring:
            if self.simulation_mode.get():
                cmd=self.last_sim_command;idx=int(self.sim_index.get() or -1)
            else:
                db=int(self.db_e.get());d=self.plc_client.db_read(db,0,2);cmd,idx=d[0],d[1]
            self.root.after(0,lambda c=cmd,i=idx:self.update_status(c,i))
            self.root.after(0,lambda c=cmd,i=idx:self.handle_plc_command(c,i))
            time.sleep(0.1)

    def add_video_mapping(self):
        try:
            idx=int(self.map_idx.get());assert 0<=idx<=255
        except:
            messagebox.showerror("Error","Enter 0-255");return
        f=filedialog.askopenfilename(filetypes=[("Videos","*.mp4 *.avi *.mov *.mkv *.wmv")])
        if not f: return
        dst=os.path.join(self.videos_directory,os.path.basename(f))
        shutil.copy2(f,dst)
        self.video_mappings[idx]=dst;self.save_mappings();self.refresh_tree()

    def remove_video_mapping(self):
        sel=self.tree.selection()
        if not sel: return
        idx=int(self.tree.item(sel[0])['values'][0])
        del self.video_mappings[idx];self.save_mappings();self.refresh_tree()

    def load_video_mappings(self):
        p=os.path.join(self.app_directory,'video_mappings.txt')
        if os.path.exists(p):
            for L in open(p):
                i,fp=L.strip().split('=',1)
                if os.path.exists(fp): self.video_mappings[int(i)]=fp
        self.refresh_tree()

    def save_mappings(self):
        p=os.path.join(self.app_directory,'video_mappings.txt')
        with open(p,'w') as f:
            for i,fp in self.video_mappings.items(): f.write(f"{i}={fp}\n")

    def refresh_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for i,fp in sorted(self.video_mappings.items()):
            self.tree.insert('',"end",values=(i,os.path.basename(fp)))

    def run(self):
        if not SNAP7_AVAILABLE: messagebox.showwarning("Warn","python-snap7 missing")
        if not VLC_AVAILABLE: messagebox.showwarning("Warn","python-vlc missing")
        self.root.mainloop()

if __name__=="__main__":
    PLCVideoController().run()
