# Plugin Loader

This application uses `carla-single` to load installed LV2 and VST plugins. Optionally, **Jalv** can be used for LV2 plugins.

---

## 🔌 Plugins Tab

This tab lists all detected plugins on your system. You can launch a plugin by **double-clicking** it or pressing **Enter**.

### Features

- **Connect**: Attempts to link audio and MIDI ports to **JACK**.
- **Autoconnect**: Automatically connects ports after launching a plugin (may cause hangs under **KDE**).
- **Run LV2 on Jalv**: Launches LV2 plugins using **Jalv** instead of `carla-single`.
- **Carla Arch**: Sets the architecture used for loading **VST** plugins.
- **Search**: Filters plugins by name.
- **Kill Apps**: Sends a termination signal to any plugin process started by the app.

---

## ⚙️ Setup Tab

Configure plugin directories, audio connections, and more.

### Options

- **VST2/3 Directories**: Add folders containing VST plugins, including those managed by **Yabridge** or located in Windows directories.
- **Keyboard/Interface Substring**: Enter part of the **JACK** name for MIDI and Audio interfaces to be used with the **Connect** feature.
- **Audio Connections Retry**: Number of attempts to connect audio ports (Recommended: `2`).
- **Terminal (Console)**: (Optional) Terminal application to use when launching plugins or processes.
- **Load VST2/3** / **Load LV2**: Select which plugin types to load.
- **Audio Connections**: Define how many audio ports to connect.

---

## 🛠️ Requirements
- **Python 3**
- **WxPython**
- **JACK/Pipewire**
- **Carla**
- **Jalv** (optional)
- Optional: **Yabridge**, **Wine**, or other tools for bridging Windows VSTs

---

## 📌 Notes

- `carla-single` is the core engine used for plugin launching.
- Some plugins or setups may cause instability under KDE with autoconnection enabled.

---

## 📷 Screenshots
![PluginLoader1](https://github.com/user-attachments/assets/51ed83e3-9bdc-4aa6-a379-6a2e26a209ba)
![PluginLoader2](https://github.com/user-attachments/assets/40576dda-0da2-4c5c-9412-a7dfc78b5a5c)
![PluginLoader3png](https://github.com/user-attachments/assets/6262953d-c3d4-4992-af08-3dbd0dc11d53)


