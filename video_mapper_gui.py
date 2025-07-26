
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import os
import shutil
import json

# Server video directory
SERVER_VIDEO_DIR = os.path.join(os.getcwd(), "videos")
# Persistent mapping file
MAPPING_FILE = os.path.join(os.getcwd(), "client_video_mappings.json")

# Ensure the directory exists
if not os.path.exists(SERVER_VIDEO_DIR):
    os.makedirs(SERVER_VIDEO_DIR)

# Load previous mappings (if any)
def load_mappings():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_mappings(mappings):
    with open(MAPPING_FILE, "w") as f:
        json.dump(mappings, f, indent=2)

# Initialize mappings - now organized by client
client_video_mappings = load_mappings()

# ---------- Tkinter UI ----------

root = tk.Tk()
root.title("Server Video Upload & Mapping - Multi-Client")
root.geometry("800x500")

selected_file = tk.StringVar()
selected_file.set("")
current_client = tk.StringVar()

def add_new_client():
    client_name = simpledialog.askstring("New Client", "Enter client name:")
    if client_name and client_name.strip():
        client_name = client_name.strip()
        if client_name not in client_video_mappings:
            client_video_mappings[client_name] = {}
            save_mappings(client_video_mappings)
            update_client_dropdown()
            client_dropdown.set(client_name)
            current_client.set(client_name)
            update_mappings_list()
            messagebox.showinfo("Success", f"Client '{client_name}' added successfully!")
        else:
            messagebox.showwarning("Client Exists", f"Client '{client_name}' already exists!")

def update_client_dropdown():
    client_names = list(client_video_mappings.keys())
    client_dropdown['values'] = client_names
    if client_names and not current_client.get():
        client_dropdown.set(client_names[0])
        current_client.set(client_names[0])

def on_client_change(*args):
    current_client.set(client_dropdown.get())
    update_mappings_list()

def upload_file():
    path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if path:
        selected_file.set(path)
        video_name.set(os.path.basename(path))

def map_video():
    client = current_client.get()
    video = selected_file.get()
    index = index_entry.get().strip()

    if not client:
        messagebox.showerror("Error", "Please select a client first.")
        return

    if not video or not index:
        messagebox.showerror("Error", "Select a video and enter an index.")
        return

    # Copy video into server directory if not already there
    video_filename = os.path.basename(video)
    server_video_path = os.path.join(SERVER_VIDEO_DIR, video_filename)
    if not os.path.exists(server_video_path) or (os.path.getsize(video) != os.path.getsize(server_video_path)):
        shutil.copy(video, server_video_path)

    # Ensure client exists in mappings
    if client not in client_video_mappings:
        client_video_mappings[client] = {}

    client_video_mappings[client][index] = video_filename
    save_mappings(client_video_mappings)
    update_mappings_list()
    messagebox.showinfo("Success", f"Video '{video_filename}' mapped to index '{index}' for client '{client}'.")

    # Reset
    video_name.set("")
    selected_file.set("")
    index_entry.delete(0, tk.END)

def update_mappings_list():
    mappings_listbox.delete(0, tk.END)
    client = current_client.get()
    if client and client in client_video_mappings:
        for idx, vid in client_video_mappings[client].items():
            mappings_listbox.insert(tk.END, f"Index '{idx}': {vid}")

def remove_selected_mapping():
    client = current_client.get()
    if not client:
        messagebox.showwarning("No Client", "Select a client first.")
        return

    sel = mappings_listbox.curselection()
    if not sel:
        messagebox.showwarning("No selection", "Select a mapping to remove.")
        return

    text = mappings_listbox.get(sel[0])
    idx = text.split("'")[1]
    if messagebox.askyesno("Confirm Delete", f"Remove video mapping for index '{idx}' from client '{client}'?"):
        if client in client_video_mappings and idx in client_video_mappings[client]:
            del client_video_mappings[client][idx]
            save_mappings(client_video_mappings)
            update_mappings_list()

def remove_client():
    client = current_client.get()
    if not client:
        messagebox.showwarning("No Client", "Select a client first.")
        return

    if messagebox.askyesno("Confirm Delete", f"Remove entire client '{client}' and all its mappings?"):
        if client in client_video_mappings:
            del client_video_mappings[client]
            save_mappings(client_video_mappings)
            update_client_dropdown()
            current_client.set("")
            if client_video_mappings:
                first_client = list(client_video_mappings.keys())[0]
                client_dropdown.set(first_client)
                current_client.set(first_client)
            update_mappings_list()

# --- Widgets ---

# Client Selection Frame
client_frame = tk.Frame(root)
client_frame.pack(pady=15)

client_label = tk.Label(client_frame, text="Select Client:", font=("Arial", 12, "bold"))
client_label.grid(row=0, column=0, padx=5)

client_dropdown = ttk.Combobox(client_frame, width=20, state="readonly")
client_dropdown.grid(row=0, column=1, padx=5)
client_dropdown.bind('<<ComboboxSelected>>', on_client_change)

add_client_btn = tk.Button(client_frame, text="Add New Client", command=add_new_client, bg="lightgreen")
add_client_btn.grid(row=0, column=2, padx=5)

remove_client_btn = tk.Button(client_frame, text="Remove Client", command=remove_client, bg="lightcoral")
remove_client_btn.grid(row=0, column=3, padx=5)

# Separator
separator1 = ttk.Separator(root, orient='horizontal')
separator1.pack(fill='x', pady=10)

# Video Mapping Frame
mapping_frame = tk.Frame(root)
mapping_frame.pack(pady=15)

upload_btn = tk.Button(mapping_frame, text="Choose Video File", command=upload_file)
upload_btn.grid(row=0, column=0, padx=5)

video_name = tk.StringVar()
video_name_label = tk.Label(mapping_frame, textvariable=video_name, width=30, relief="sunken")
video_name_label.grid(row=0, column=1, padx=5)

index_label = tk.Label(mapping_frame, text="Enter Index:")
index_label.grid(row=0, column=2, padx=5)
index_entry = tk.Entry(mapping_frame, width=15)
index_entry.grid(row=0, column=3, padx=5)

map_btn = tk.Button(mapping_frame, text="Map Video to Index", command=map_video, bg="lightblue")
map_btn.grid(row=0, column=4, padx=5)

# Separator
separator2 = ttk.Separator(root, orient='horizontal')
separator2.pack(fill='x', pady=10)

# Current Client Mappings Display
display_frame = tk.Frame(root)
display_frame.pack(pady=10)

current_client_label = tk.Label(display_frame, text="Current Client Mappings:", font=("Arial", 11, "bold"))
current_client_label.pack()

list_frame = tk.Frame(display_frame)
list_frame.pack(pady=5)

mappings_listbox = tk.Listbox(list_frame, width=80, height=12)
mappings_listbox.pack(side=tk.LEFT)

scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
scrollbar.config(command=mappings_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
mappings_listbox.config(yscrollcommand=scrollbar.set)

remove_mapping_btn = tk.Button(display_frame, text="Remove Selected Mapping", command=remove_selected_mapping, fg="red")
remove_mapping_btn.pack(pady=5)

# Initialize
update_client_dropdown()
update_mappings_list()

root.mainloop()
